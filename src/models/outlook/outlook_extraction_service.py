"""
Outlookからのメール抽出サービス

責務:
- メール抽出タスクの実行管理
- 抽出条件に基づくメールの取得
- メール処理のワークフロー制御
- 進捗状況の管理
- Outlookスナップショットの作成と管理

主なメソッド:
- start_extraction: 抽出作業の開始
- create_snapshot: Outlookスナップショットの作成
- get_extraction_conditions: 抽出条件の取得
- _process_mail_item: 個別メールの処理
- _process_attachments: 添付ファイルの処理
- _process_ai_review: AIレビューの処理
- _update_mail_task_status: タスクステータスの更新

連携:
- OutlookClient: メールデータの取得
- OutlookItemModel: メールデータの保存
- データベース:
  - items.db（mail_tasks, task_progressテーブル）
  - outlook.db（extraction_conditionsテーブル）
"""

import os
from typing import Optional

from src.core.database import DatabaseManager
from src.core.logger import get_logger
from src.models.outlook.outlook_client import OutlookClient
from src.models.outlook.outlook_item_model import OutlookItemModel
from src.util.object_util import get_safe


class OutlookExtractionService:
    """Outlookからのメール抽出サービス"""

    def __init__(self, task_id: str):
        """初期化"""
        self.task_id = task_id
        self.logger = get_logger()
        self.outlook_client = OutlookClient()
        self.items_db = None
        self.outlook_db = None
        self.tasks_db = None

    def initialize(self) -> bool:
        """データベース接続の初期化"""
        try:
            # items.dbの接続
            items_db_path = f"data/tasks/{self.task_id}/items.db"
            self.items_db = DatabaseManager(items_db_path)

            # outlook.dbの接続
            outlook_db_path = "data/outlook.db"
            self.outlook_db = DatabaseManager(outlook_db_path)

            # tasks.dbの接続
            tasks_db_path = "data/tasks.db"
            if not os.path.exists(tasks_db_path):
                self.logger.error("tasks.dbが見つかりません", path=tasks_db_path)
                return False

            self.tasks_db = DatabaseManager(tasks_db_path)

            return True
        except Exception as e:
            self.logger.error("データベース接続の初期化に失敗", error=str(e))
            return False

    def cleanup(self):
        """リソースの解放"""
        if self.items_db:
            self.items_db.disconnect()
        if self.outlook_db:
            self.outlook_db.disconnect()
        if self.tasks_db:
            self.tasks_db.disconnect()

    def get_extraction_conditions(self) -> Optional[dict]:
        """
        抽出条件を取得する

        Returns:
            Optional[dict]: 抽出条件
        """
        try:
            # tasks.dbから抽出条件を取得
            if not self.tasks_db:
                self.logger.error(f"tasks.dbが接続されていません")
                return None

            # task_infoテーブルから抽出条件を取得
            query = """
                SELECT 
                    from_folder_id,
                    start_date,
                    end_date,
                    file_download,
                    exclude_extensions,
                    ai_review
                FROM task_info
                WHERE id = ?
            """
            result = self.tasks_db.execute_query(query, (self.task_id,))

            if not result:
                self.logger.error(f"タスク情報が見つかりません: {self.task_id}")
                return None

            task_info = result[0]

            # 日付を取得
            start_date = get_safe(task_info, "start_date")
            end_date = get_safe(task_info, "end_date")

            # Outlookのフィルター形式に変換
            date_filter = ""
            if start_date and end_date:
                date_filter = f"[ReceivedTime] >= '{start_date}' AND [ReceivedTime] <= '{end_date}'"
            elif start_date:
                date_filter = f"[ReceivedTime] >= '{start_date}'"
            elif end_date:
                date_filter = f"[ReceivedTime] <= '{end_date}'"

            # get_safeを使用して安全にデータを取得
            conditions = {
                "folder_id": get_safe(task_info, "from_folder_id"),
                "date_filter": date_filter,
                "file_download": bool(get_safe(task_info, "file_download", False)),
                "exclude_extensions": get_safe(task_info, "exclude_extensions"),
                "ai_review": bool(get_safe(task_info, "ai_review", False)),
            }

            self.logger.info(f"抽出条件を取得しました: {conditions}")
            return conditions

        except Exception as e:
            self.logger.error(f"抽出条件の取得に失敗: {str(e)}")
            return None

    def create_snapshot(self) -> bool:
        """
        outlook.dbのfoldersテーブルの状態をitems.dbのoutlook_snapshotテーブルに記録する

        Returns:
            bool: 記録が成功したかどうか
        """
        try:
            self.logger.info("Outlookスナップショット作成開始", task_id=self.task_id)

            # トランザクション開始
            self.items_db.begin_transaction()
            self.outlook_db.begin_transaction()

            try:
                # outlook.dbからfoldersテーブルのデータを取得
                folders_data = self.outlook_db.execute_query("SELECT * FROM folders")

                # outlook_snapshotテーブルにデータを挿入
                for folder in folders_data:
                    query = """
                    INSERT INTO outlook_snapshot (
                        entry_id, store_id, name, path, parent_folder_id,
                        folder_type, folder_class, item_count, unread_count,
                        snapshot_time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    """
                    params = (
                        get_safe(folder, "entry_id"),
                        get_safe(folder, "store_id"),
                        get_safe(folder, "name"),
                        get_safe(folder, "path"),
                        get_safe(folder, "parent_folder_id"),
                        get_safe(folder, "folder_type"),
                        get_safe(folder, "folder_class"),
                        get_safe(folder, "item_count"),
                        get_safe(folder, "unread_count"),
                    )
                    self.items_db.execute_update(query, params)

                # トランザクションをコミット
                self.items_db.commit()
                self.outlook_db.commit()
                self.logger.info(
                    "Outlookスナップショット作成成功", task_id=self.task_id
                )
                return True

            except Exception as e:
                # エラー時はトランザクションをロールバック
                self.items_db.rollback()
                self.outlook_db.rollback()
                raise e

        except Exception as e:
            self.logger.error(
                "Outlookスナップショット作成エラー", task_id=self.task_id, error=str(e)
            )
            return False

    def _create_extraction_plan(self) -> bool:
        """
        メールアイテムの抽出計画を作成する

        Returns:
            bool: 作成が成功したかどうか
        """
        try:
            self.logger.info("抽出計画作成開始", task_id=self.task_id)

            # トランザクション開始
            self.items_db.begin_transaction()

            try:
                # task_infoテーブルからタスク情報を取得 (tasks.dbにある)
                task_info_query = """
                SELECT * FROM task_info WHERE id = ?
                """
                # 共有のtasks.dbから情報を取得
                if not self.tasks_db:
                    self.logger.error("tasks.dbが接続されていません")
                    self.items_db.rollback()
                    return False

                task_info = self.tasks_db.execute_query(
                    task_info_query, (self.task_id,)
                )

                if not task_info:
                    self.logger.error(
                        "タスク情報が見つかりません", task_id=self.task_id
                    )
                    self.items_db.rollback()
                    return False

                task = task_info[0]
                from_folder_id = get_safe(task, "from_folder_id")
                from_folder_name = get_safe(task, "from_folder_name")
                start_date = get_safe(task, "start_date")
                end_date = get_safe(task, "end_date")
                exclude_extensions = get_safe(task, "exclude_extensions")

                # outlook_snapshotテーブルから対象フォルダのメールアイテム情報を取得
                # この段階では実際のメールデータではなく、計画に必要な情報のみを取得
                folder_info_query = """
                SELECT entry_id, name, item_count
                FROM outlook_snapshot
                WHERE entry_id = ?
                """
                folder_info = self.items_db.execute_query(
                    folder_info_query, (from_folder_id,)
                )

                if not folder_info:
                    self.logger.error(
                        "スナップショットにフォルダ情報が見つかりません",
                        task_id=self.task_id,
                        folder_id=from_folder_id,
                    )
                    self.items_db.rollback()
                    return False

                folder = folder_info[0]
                total_messages = get_safe(folder, "item_count", 0)

                if total_messages == 0:
                    self.logger.warning(
                        "対象メールがありません",
                        task_id=self.task_id,
                        from_folder=from_folder_name,
                        start_date=start_date,
                        end_date=end_date,
                    )
                    self.items_db.rollback()
                    return False

                # Outlookクライアントを使用して対象メールの基本情報のみを取得
                outlook_client = OutlookClient()
                mail_items_basic = outlook_client.get_mail_list(
                    from_folder_id,
                    filter_criteria=f"[ReceivedTime] >= '{start_date}' AND [ReceivedTime] <= '{end_date}'",
                )

                # 抽出条件を記録
                extraction_conditions_query = """
                INSERT INTO extraction_conditions (
                    task_id, from_folder_id, from_folder_name,
                    start_date, end_date, exclude_extensions,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                """
                self.items_db.execute_update(
                    extraction_conditions_query,
                    (
                        self.task_id,
                        from_folder_id,
                        from_folder_name,
                        start_date,
                        end_date,
                        exclude_extensions,
                    ),
                )

                # mail_tasksテーブルに各メールアイテムの抽出計画を記録
                mail_tasks_query = """
                INSERT INTO mail_tasks (
                    task_id, message_id, subject, sent_time,
                    status, mail_fetch_status, attachment_status,
                    ai_review_status, created_at
                ) VALUES (?, ?, ?, ?, 'pending', 'pending', 'pending', 'pending', datetime('now'))
                """

                for mail_item in mail_items_basic:
                    self.items_db.execute_update(
                        mail_tasks_query,
                        (
                            self.task_id,
                            get_safe(mail_item, "EntryID"),
                            get_safe(mail_item, "Subject"),
                            get_safe(mail_item, "SentOn")
                            or get_safe(mail_item, "ReceivedTime"),
                        ),
                    )

                # task_progressテーブルに進捗状況を記録
                # トリガーで自動的に追加されるので削除
                # task_progress_query = """
                # INSERT INTO task_progress (
                #     task_id, total_messages, processed_messages,
                #     successful_messages, failed_messages, skipped_messages,
                #     status, last_updated_at
                # ) VALUES (?, ?, 0, 0, 0, 0, 'pending', datetime('now'))
                # """
                # self.items_db.execute_update(
                #    task_progress_query, (self.task_id, total_messages)
                # )

                # トランザクションをコミット
                self.items_db.commit()

                self.logger.info(
                    "抽出計画作成成功",
                    task_id=self.task_id,
                    total_messages=len(mail_items_basic),
                    from_folder=from_folder_name,
                    start_date=start_date,
                    end_date=end_date,
                )
                return True

            except Exception as e:
                # エラー時はトランザクションをロールバック
                self.items_db.rollback()
                raise e

        except Exception as e:
            self.logger.error("抽出計画作成エラー", task_id=self.task_id, error=str(e))
            return False

    def start_extraction(self) -> bool:
        """抽出作業の開始"""
        try:
            # まず、Outlookのスナップショットを作成
            if not self.create_snapshot():
                self.logger.error("Outlookスナップショットの作成に失敗しました")
                return False

            # 次に、抽出計画を作成
            if not self._create_extraction_plan():
                self.logger.error("抽出計画の作成に失敗しました")
                return False

            # 抽出条件の取得
            conditions = self.get_extraction_conditions()
            if not conditions:
                return False

            # OutlookItemModelの初期化
            item_model = OutlookItemModel()

            # バッチ処理用の準備
            chunk_size = item_model._calculate_chunk_size()

            # メールタスクをチャンク処理するための準備
            mail_tasks_query = """
            SELECT id, task_id, message_id 
            FROM mail_tasks 
            WHERE task_id = ? AND status = 'pending'
            """
            mail_tasks = self.items_db.execute_query(mail_tasks_query, (self.task_id,))

            self.logger.info(f"抽出対象のメールタスク数: {len(mail_tasks)}")

            # タスク状態を処理中に更新
            update_task_status_query = """
            UPDATE task_progress SET status = 'processing', started_at = datetime('now')
            WHERE task_id = ?
            """
            self.items_db.execute_update(update_task_status_query, (self.task_id,))

            # チャンク処理
            for i in range(0, len(mail_tasks), chunk_size):
                chunk = mail_tasks[i : i + chunk_size]
                self.logger.info(
                    f"チャンク処理開始: {i+1}～{i+len(chunk)}/{len(mail_tasks)}"
                )

                # チャンク内のメールをOutlookから取得して保存
                for task in chunk:
                    # タスクステータスを処理中に更新
                    self._update_mail_task_status(
                        get_safe(task, "id"),
                        "processing",
                        mail_fetch_status="processing",
                    )

                    # メール本体を取得
                    mail_id = get_safe(task, "message_id")
                    if not self._process_mail_item(mail_id):
                        self._update_mail_task_status(
                            get_safe(task, "id"),
                            "error",
                            error_message="メール処理に失敗しました",
                            mail_fetch_status="error",
                        )

                self.logger.info(
                    f"チャンク処理完了: {i+1}～{i+len(chunk)}/{len(mail_tasks)}"
                )

            # 添付ファイル処理
            if conditions.get("file_download", False):
                self._process_all_attachments()

            # AIレビュー処理
            if conditions.get("ai_review", False):
                self._process_all_ai_reviews()

            self.logger.info("抽出作業が完了しました")
            return True

        except Exception as e:
            self.logger.error("抽出作業の実行に失敗", error=str(e))
            return False

    def _update_mail_task_status(
        self,
        task_id: int,
        status: str,
        error_message: Optional[str] = None,
        mail_fetch_status: Optional[str] = None,
        attachment_status: Optional[str] = None,
        ai_review_status: Optional[str] = None,
    ) -> bool:
        """
        メールタスクのステータス更新

        Args:
            task_id: メールタスクID
            status: 全体ステータス
            error_message: エラーメッセージ
            mail_fetch_status: メール取得ステータス
            attachment_status: 添付ファイル処理ステータス
            ai_review_status: AIレビューステータス

        Returns:
            bool: 更新が成功したかどうか
        """
        try:
            # UPDATE文の構築
            query = "UPDATE mail_tasks SET status = ?"
            params = [status]

            if error_message is not None:
                query += ", error_message = ?"
                params.append(error_message)

            if mail_fetch_status is not None:
                query += ", mail_fetch_status = ?"
                params.append(mail_fetch_status)

            if attachment_status is not None:
                query += ", attachment_status = ?"
                params.append(attachment_status)

            if ai_review_status is not None:
                query += ", ai_review_status = ?"
                params.append(ai_review_status)

            # 時間情報の更新
            if status == "processing" and mail_fetch_status == "processing":
                query += ", started_at = datetime('now')"

            if status in ["completed", "error", "skipped"]:
                query += ", completed_at = datetime('now')"

            # WHERE句
            query += " WHERE id = ?"
            params.append(task_id)

            # クエリ実行
            self.items_db.execute_update(query, tuple(params))
            return True

        except Exception as e:
            self.logger.error(f"タスクステータス更新エラー: {str(e)}")
            return False

    def _process_all_attachments(self) -> bool:
        """
        全ての添付ファイルを処理する

        Returns:
            bool: 処理が成功したかどうか
        """
        try:
            # 添付ファイル処理が必要なメールタスクを取得
            query = """
            SELECT id, task_id, message_id, mail_id
            FROM mail_tasks 
            WHERE task_id = ? 
              AND mail_fetch_status = 'success'
              AND attachment_status = 'pending'
            """
            tasks = self.items_db.execute_query(query, (self.task_id,))

            if not tasks:
                self.logger.info("添付ファイル処理が必要なメールはありません")
                return True

            # OutlookItemModelの初期化
            item_model = OutlookItemModel()
            chunk_size = item_model._calculate_chunk_size()

            # チャンク処理
            for i in range(0, len(tasks), chunk_size):
                chunk = tasks[i : i + chunk_size]
                self.logger.info(
                    f"添付ファイル処理チャンク: {i+1}～{i+len(chunk)}/{len(tasks)}"
                )

                for task in chunk:
                    task_id = get_safe(task, "id")
                    mail_id = get_safe(task, "mail_id")

                    # ステータス更新
                    self._update_mail_task_status(
                        task_id, "processing", attachment_status="processing"
                    )

                    # 添付ファイル保存先パス
                    save_path = f"data/tasks/{self.task_id}/attachments/{mail_id}"

                    if item_model.process_attachments(
                        mail_id, {"HasAttachments": True}, save_path
                    ):
                        self._update_mail_task_status(
                            task_id, "processing", attachment_status="success"
                        )
                    else:
                        self._update_mail_task_status(
                            task_id,
                            "processing",
                            attachment_status="error",
                            error_message="添付ファイル処理に失敗しました",
                        )

            return True

        except Exception as e:
            self.logger.error(f"添付ファイル一括処理エラー: {str(e)}")
            return False

    def _process_all_ai_reviews(self) -> bool:
        """
        全てのAIレビューを処理する

        Returns:
            bool: 処理が成功したかどうか
        """
        try:
            # AIレビュー処理が必要なメールタスクを取得
            query = """
            SELECT id, task_id, message_id, mail_id
            FROM mail_tasks 
            WHERE task_id = ? 
              AND mail_fetch_status = 'success'
              AND ai_review_status = 'pending'
            """
            tasks = self.items_db.execute_query(query, (self.task_id,))

            if not tasks:
                self.logger.info("AIレビュー処理が必要なメールはありません")
                return True

            # OutlookItemModelの初期化
            item_model = OutlookItemModel()
            chunk_size = item_model._calculate_chunk_size()

            # チャンク処理
            for i in range(0, len(tasks), chunk_size):
                chunk = tasks[i : i + chunk_size]
                self.logger.info(
                    f"AIレビュー処理チャンク: {i+1}～{i+len(chunk)}/{len(tasks)}"
                )

                for task in chunk:
                    task_id = get_safe(task, "id")
                    mail_id = get_safe(task, "mail_id")

                    # ステータス更新
                    self._update_mail_task_status(
                        task_id, "processing", ai_review_status="processing"
                    )

                    # AIレビュー処理
                    if self._process_ai_review(mail_id):
                        self._update_mail_task_status(
                            task_id, "completed", ai_review_status="success"
                        )
                    else:
                        self._update_mail_task_status(
                            task_id,
                            "error",
                            ai_review_status="error",
                            error_message="AIレビュー処理に失敗しました",
                        )

            return True

        except Exception as e:
            self.logger.error(f"AIレビュー一括処理エラー: {str(e)}")
            return False

    def _process_mail_item(self, mail_item: dict) -> bool:
        """メールアイテムの処理"""
        try:
            # メールコンテンツの抽出
            mail_model = self._extract_mail_content(get_safe(mail_item, "EntryID"))
            if not mail_model:
                return False

            # 添付ファイルの処理
            if self.get_extraction_conditions().get("file_download", False):
                if not self._process_attachments(mail_model):
                    self.logger.warning(
                        f"添付ファイルの処理に失敗: {get_safe(mail_item, 'EntryID')}"
                    )

            # AIレビューの処理
            if self.get_extraction_conditions().get("ai_review", False):
                if not self._process_ai_review(mail_model):
                    self.logger.warning(
                        f"AIレビューの処理に失敗: {get_safe(mail_item, 'EntryID')}"
                    )

            # メールアイテムの保存
            if not self._save_mail_item(mail_model):
                return False

            return True

        except Exception as e:
            self.logger.error(f"メール処理中にエラーが発生: {str(e)}")
            return False

    def _extract_mail_content(self, entry_id: str) -> Optional[OutlookItemModel]:
        """メールコンテンツの抽出"""
        pass

    def _save_mail_item(self, mail_item: OutlookItemModel) -> bool:
        """メールアイテムの保存"""
        pass

    def _process_attachments(self, mail_item: OutlookItemModel) -> bool:
        """添付ファイルの処理"""
        pass

    def _process_ai_review(self, mail_item: OutlookItemModel) -> bool:
        """AIレビューの処理"""
        pass

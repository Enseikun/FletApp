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

import datetime
import os
import re
import uuid
from typing import Optional

from markdownify import markdownify

from src.core.database import DatabaseManager
from src.core.logger import get_logger
from src.models.outlook.outlook_client import OutlookClient
from src.models.outlook.outlook_item_model import OutlookItemModel
from src.models.outlook.outlook_service import OutlookService
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

    def _format_date_string(self, date_value) -> str:
        """
        日付値を文字列形式に変換する

        Args:
            date_value: 変換する日付値（文字列またはdatetimeオブジェクト）

        Returns:
            str: 変換後の日付文字列（YYYY-MM-DD HH:MM:SS形式）
        """
        if not date_value:
            return ""

        try:
            # datetimeオブジェクトの場合は文字列に変換
            if hasattr(date_value, "strftime"):
                return date_value.strftime("%Y-%m-%d %H:%M:%S")
            # 既に文字列の場合はそのまま使用
            return str(date_value)
        except AttributeError:
            # 変換できない場合は文字列としてそのまま返す
            return str(date_value)

    def _format_outlook_date_filter(self, date_str: str) -> str:
        """
        日付文字列をOutlookフィルター用に変換する

        Args:
            date_str: 元の日付文字列

        Returns:
            str: Outlook用に変換された日付文字列
        """
        if not date_str:
            return ""

        parts = date_str.replace("-", "/").rsplit(":", 1)
        return parts[0] if len(parts) > 1 else date_str.replace("-", "/")

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

            # 日付形式を変換（共通関数を使用）
            start_date_formatted = self._format_outlook_date_filter(start_date)
            end_date_formatted = self._format_outlook_date_filter(end_date)

            # Outlookのフィルター形式に変換
            date_filter = ""
            if start_date and end_date:
                date_filter = f"[ReceivedTime] >= '{start_date_formatted}' AND [ReceivedTime] <= '{end_date_formatted}'"
            elif start_date:
                date_filter = f"[ReceivedTime] >= '{start_date_formatted}'"
            elif end_date:
                date_filter = f"[ReceivedTime] <= '{end_date_formatted}'"

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

                if not folders_data:
                    self.logger.warning(
                        "フォルダデータが見つかりません", task_id=self.task_id
                    )

                # スナップショットのデータが既に存在するか確認
                existing_count_result = self.items_db.execute_query(
                    "SELECT COUNT(*) as count FROM outlook_snapshot"
                )
                existing_count = (
                    existing_count_result[0].get("count", 0)
                    if existing_count_result
                    else 0
                )

                # データが既に存在する場合は削除
                if existing_count > 0:
                    self.logger.info(
                        "既存のスナップショットデータを削除します", count=existing_count
                    )
                    self.items_db.execute_update("DELETE FROM outlook_snapshot")

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
                self.logger.error(
                    "スナップショット作成中のエラー（トランザクション内）",
                    task_id=self.task_id,
                    error=repr(e),
                    error_type=type(e).__name__,
                    error_details=str(e),
                )
                raise e

        except Exception as e:
            self.logger.error(
                "Outlookスナップショット作成エラー",
                task_id=self.task_id,
                error=repr(e),
                error_type=type(e).__name__,
                error_details=str(e),
            )
            return False

    def _clean_unicode_text(self, text: str) -> str:
        """
        無効なUnicode文字（サロゲートペア文字）を削除または置換する

        Args:
            text: 処理するテキスト

        Returns:
            str: 無効な文字を削除したテキスト
        """
        if not isinstance(text, str):
            return ""

        try:
            # サロゲートペア文字をチェック
            # unicodedata.is_normalized使用も可能だが、より直接的に対処
            # 文字列をUTF-8で一度エンコードしてデコードし、エラーは置換する
            cleaned_text = text.encode("utf-8", "replace").decode("utf-8")

            # パターンD800-DFFF（サロゲート領域）の文字を削除
            # サロゲートペアになっていない不正なサロゲート文字を削除
            cleaned_text = re.sub(r"[\uD800-\uDFFF]", "", cleaned_text)

            return cleaned_text
        except Exception as e:
            self.logger.error(f"Unicode文字列のクリーニングに失敗: {str(e)}")
            # エラーが発生した場合は、可能な限りエンコード可能な部分だけを返す
            return text.encode("ascii", "ignore").decode("ascii")

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
                # 既存の抽出計画をチェック
                existing_conditions = self.items_db.execute_query(
                    "SELECT COUNT(*) as count FROM extraction_conditions WHERE task_id = ?",
                    (self.task_id,),
                )

                existing_mail_tasks = self.items_db.execute_query(
                    "SELECT COUNT(*) as count FROM mail_tasks WHERE task_id = ?",
                    (self.task_id,),
                )

                # 既に抽出計画が存在する場合は削除して再作成
                existing_conditions_count = (
                    existing_conditions[0].get("count", 0) if existing_conditions else 0
                )
                if existing_conditions_count > 0:
                    self.logger.info("既存の抽出条件を削除します", task_id=self.task_id)
                    self.items_db.execute_update(
                        "DELETE FROM extraction_conditions WHERE task_id = ?",
                        (self.task_id,),
                    )

                existing_mail_tasks_count = (
                    existing_mail_tasks[0].get("count", 0) if existing_mail_tasks else 0
                )
                if existing_mail_tasks_count > 0:
                    self.logger.info(
                        "既存のメールタスクを削除します",
                        task_id=self.task_id,
                        count=existing_mail_tasks_count,
                    )
                    self.items_db.execute_update(
                        "DELETE FROM mail_tasks WHERE task_id = ?", (self.task_id,)
                    )

                # task_progressが存在する場合は削除
                self.items_db.execute_update(
                    "DELETE FROM task_progress WHERE task_id = ?", (self.task_id,)
                )

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

                # OutlookItemModelを使用して対象メールの基本情報のみを取得
                outlook_item_model = OutlookItemModel()

                # 日付形式を変換（共通関数を使用）
                start_date_formatted = self._format_outlook_date_filter(start_date)
                end_date_formatted = self._format_outlook_date_filter(end_date)

                # ジェネレータからすべてのチャンクを取得してリストに結合
                mail_items_basic = []
                for chunk in outlook_item_model.get_mail_items(
                    from_folder_id,
                    filter_criteria=f"[ReceivedTime] >= '{start_date_formatted}' AND [ReceivedTime] <= '{end_date_formatted}'",
                ):
                    mail_items_basic.extend(chunk)

                # 抽出条件を記録
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                extraction_conditions_query = """
                INSERT INTO extraction_conditions (
                    task_id, from_folder_id, from_folder_name,
                    start_date, end_date, exclude_extensions,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
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
                        current_time,
                    ),
                )

                # mail_tasksテーブルに各メールアイテムの抽出計画を記録
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                mail_tasks_query = """
                INSERT INTO mail_tasks (
                    task_id, message_id, subject, sent_time,
                    status, mail_fetch_status, attachment_status,
                    ai_review_status, created_at
                ) VALUES (?, ?, ?, ?, 'pending', 'pending', 'pending', 'pending', ?)
                """

                for mail_item in mail_items_basic:
                    # 日時データを取得して変換
                    sent_time = get_safe(mail_item, "SentOn") or get_safe(
                        mail_item, "ReceivedTime"
                    )

                    # 共通関数を使用して日時を文字列に変換
                    sent_time_str = self._format_date_string(sent_time)

                    # 無効なUnicode文字（サロゲートペア）を含む件名をクリーニング
                    subject = get_safe(mail_item, "Subject")
                    cleaned_subject = self._clean_unicode_text(subject)

                    # サロゲートペア文字が削除された場合にログに記録
                    if subject != cleaned_subject:
                        self.logger.info(
                            f"件名から無効なUnicode文字を削除しました: {subject} -> {cleaned_subject}",
                            task_id=self.task_id,
                        )

                    self.items_db.execute_update(
                        mail_tasks_query,
                        (
                            self.task_id,
                            get_safe(mail_item, "EntryID"),
                            cleaned_subject,
                            sent_time_str,
                            current_time,
                        ),
                    )

                # task_progressテーブルに明示的に進捗状況を記録（初期状態）
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                task_progress_query = """
                INSERT OR REPLACE INTO task_progress (
                    task_id, 
                    total_messages,
                    status,
                    last_updated_at
                ) VALUES (?, ?, 'pending', ?)
                """
                self.items_db.execute_update(
                    task_progress_query,
                    (self.task_id, len(mail_items_basic), current_time),
                )

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
            # スナップショットの存在を確認
            snapshot_exists = False
            try:
                snapshot_count_query = "SELECT COUNT(*) as count FROM outlook_snapshot"
                snapshot_result = self.items_db.execute_query(snapshot_count_query)
                if snapshot_result and snapshot_result[0].get("count", 0) > 0:
                    snapshot_exists = True
                    self.logger.info("既存のOutlookスナップショットを検出しました")
            except Exception as e:
                self.logger.warning(f"スナップショット確認中にエラー: {str(e)}")
                # エラーが発生した場合は存在しないと仮定
                snapshot_exists = False

            # スナップショットが存在しない場合のみ作成
            if not snapshot_exists:
                if not self.create_snapshot():
                    self.logger.error("Outlookスナップショットの作成に失敗しました")
                    # タスク状態を失敗に更新
                    self._update_extraction_status(
                        "error", "Outlookスナップショットの作成に失敗しました"
                    )
                    return False
            else:
                self.logger.info("既存のスナップショットを使用します")

            # 次に、抽出計画を作成
            if not self._create_extraction_plan():
                self.logger.error("抽出計画の作成に失敗しました")
                # タスク状態を失敗に更新
                self._update_extraction_status("error", "抽出計画の作成に失敗しました")
                return False

            # 抽出条件の取得
            conditions = self.get_extraction_conditions()
            if not conditions:
                # タスク状態を失敗に更新
                self._update_extraction_status("error", "抽出条件の取得に失敗しました")
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
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_task_status_query = """
            UPDATE task_progress SET status = 'processing', started_at = ?, last_updated_at = ?
            WHERE task_id = ?
            """
            self.items_db.execute_update(
                update_task_status_query, (current_time, current_time, self.task_id)
            )

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
            # タスク状態を完了に更新
            self._update_extraction_status(
                "completed", "メール抽出が正常に完了しました"
            )
            return True

        except Exception as e:
            self.logger.error("抽出作業の実行に失敗", error=str(e))
            # タスク状態を失敗に更新
            self._update_extraction_status("error", f"抽出作業の実行に失敗: {str(e)}")
            return False

    def _update_extraction_status(self, status: str, message: str = "") -> bool:
        """
        抽出タスク全体のステータスを更新する

        Args:
            status: ステータス ("completed", "error", "processing")
            message: 状態メッセージ

        Returns:
            bool: 更新が成功したかどうか
        """
        try:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # task_progressテーブルにステータスを記録
            query = """
            UPDATE task_progress 
            SET status = ?, last_error = ?, 
                completed_at = CASE WHEN ? IN ('completed', 'error') THEN ? ELSE completed_at END,
                last_updated_at = ?
            WHERE task_id = ?
            """
            self.items_db.execute_update(
                query,
                (status, message, status, current_time, current_time, self.task_id),
            )

            self.logger.info(
                f"抽出タスクのステータスを更新: {status}",
                task_id=self.task_id,
                status_message=message,
            )
            return True

        except Exception as e:
            self.logger.error(f"抽出タスクのステータス更新に失敗: {str(e)}")
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
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
                query += ", started_at = ?"
                params.append(current_time)

            if status in ["completed", "error", "skipped"]:
                query += ", completed_at = ?"
                params.append(current_time)

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
              AND message_id IN (
                SELECT entry_id FROM mail_items 
                WHERE message_type != 'msg'  -- .msg形式のメールは除外（既に処理済みのため）
              )
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
                    message_id = get_safe(task, "message_id")
                    mail_id = (
                        get_safe(task, "mail_id") or message_id
                    )  # mail_idがなければmessage_idを使用

                    # ステータス更新
                    self._update_mail_task_status(
                        task_id, "processing", attachment_status="processing"
                    )

                    # メールアイテムのデータを取得
                    mail_query = """
                    SELECT 
                        entry_id, subject, folder_id, has_attachments, attachment_count
                    FROM mail_items 
                    WHERE entry_id = ?
                    """
                    mail_result = self.items_db.execute_query(mail_query, (mail_id,))

                    if not mail_result:
                        self.logger.error(f"メールデータが見つかりません: {mail_id}")
                        self._update_mail_task_status(
                            task_id,
                            "error",
                            attachment_status="error",
                            error_message="メールデータが見つかりません",
                        )
                        continue

                    mail_data = mail_result[0]

                    # 添付ファイル処理を実行
                    if self._process_attachment_for_mail(mail_data):
                        self.logger.info(
                            f"メール {mail_id} の添付ファイル処理が完了しました"
                        )
                    else:
                        self.logger.error(
                            f"メール {mail_id} の添付ファイル処理に失敗しました"
                        )
                        self._update_mail_task_status(
                            task_id,
                            "error",
                            attachment_status="error",
                            error_message="添付ファイル処理に失敗しました",
                        )

            self.logger.info("すべての添付ファイル処理が完了しました")
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
                    message_id = get_safe(task, "message_id")

                    # ステータス更新
                    self._update_mail_task_status(
                        task_id, "processing", ai_review_status="processing"
                    )

                    # AIレビュー処理
                    if self._process_ai_review(message_id):
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

    def _process_mail_item(self, entry_id: str) -> bool:
        """
        メールアイテムの処理

        Args:
            entry_id: メールのEntryID

        Returns:
            bool: 処理が成功したかどうか
        """
        try:
            # メールコンテンツの抽出
            mail_data = self._extract_mail_content(entry_id)

            # 暫定対応: OutlookItemModelを使って直接メールを取得
            self.logger.info(f"メールID {entry_id} の処理開始")

            # 本来の処理コード (未実装部分)
            if not mail_data:
                return False

            # メールアイテムの保存
            if not self._save_mail_item(mail_data):
                return False

            # 抽出条件を一度だけ取得
            conditions = self.get_extraction_conditions()
            if not conditions:
                return False

            # 添付ファイルの処理 - mail_dataのhas_attachmentsが真の場合のみ処理
            if conditions.get("file_download", False) and mail_data.get(
                "has_attachments", False
            ):
                if not self._process_attachment_for_mail(
                    mail_data, conditions.get("exclude_extensions", "")
                ):
                    self.logger.warning(f"添付ファイルの処理に失敗: {entry_id}")

            # AIレビューの処理
            if conditions.get("ai_review", False):
                if not self._process_ai_review(entry_id):
                    self.logger.warning(f"AIレビューの処理に失敗: {entry_id}")

            return True

        except Exception as e:
            self.logger.error(f"メール処理中にエラーが発生: {str(e)}")
            return False

    def _process_attachment_for_mail(
        self, mail_data: dict, exclude_extensions: str = ""
    ) -> bool:
        """
        単一メールの添付ファイルを処理する

        Args:
            mail_data: メールデータ
            exclude_extensions: 除外する拡張子（カンマ区切り）

        Returns:
            bool: 処理が成功したかどうか
        """
        if not mail_data or not mail_data.get("has_attachments"):
            # 添付ファイルがない場合は成功として扱う
            return True

        try:
            mail_id = mail_data.get("entry_id")
            if not mail_id:
                self.logger.error("メールIDがありません")
                return False

            # 添付ファイル保存先ディレクトリを絶対パスで作成
            app_root = os.path.abspath(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                )
            )
            save_dir = os.path.abspath(
                os.path.join(app_root, "data", "tasks", self.task_id, "attachments")
            )
            os.makedirs(save_dir, exist_ok=True)
            self.logger.info(
                f"添付ファイル保存先ディレクトリを作成しました: {save_dir} (絶対パス)"
            )

            # OutlookServiceを使用してメールアイテムを取得
            outlook_service = OutlookService()
            mail_item = outlook_service.get_item_by_id(mail_id)

            if not mail_item:
                self.logger.error(f"メールアイテムの取得に失敗: {mail_id}")
                return False

            if not hasattr(mail_item, "Attachments"):
                self.logger.error("添付ファイル処理: Attachmentsプロパティがありません")
                return False

            # 添付ファイルの保存
            attachments = mail_item.Attachments
            if not attachments or attachments.Count == 0:
                self.logger.warning(f"添付ファイルが見つかりませんでした: {mail_id}")
                return True

            # 実際に処理した添付ファイルの数
            processed_count = 0
            self.logger.info(
                f"添付ファイル処理: {attachments.Count}個の添付ファイルを処理します"
            )

            for j in range(1, attachments.Count + 1):  # Outlookのインデックスは1始まり
                try:
                    attachment = attachments.Item(j)
                    file_name = attachment.FileName
                    self.logger.info(f"添付ファイル処理中: {file_name}")

                    # 除外拡張子のチェック
                    if exclude_extensions:
                        extension = os.path.splitext(file_name)[1].lower()
                        if extension and extension[1:] in [
                            ext.strip().lower() for ext in exclude_extensions.split(",")
                        ]:
                            self.logger.info(
                                f"除外拡張子のため保存をスキップ: {file_name}"
                            )
                            continue

                    # 添付ファイル保存パスを絶対パスで生成
                    file_path = os.path.abspath(os.path.join(save_dir, file_name))

                    # パスの長さをログ出力
                    self.logger.info(f"添付ファイルの保存パス: {file_path}")
                    self.logger.info(f"パスの長さ: {len(file_path)}文字")

                    # 確実にディレクトリが存在することを再確認
                    dir_path = os.path.dirname(file_path)
                    if not os.path.exists(dir_path):
                        self.logger.info(f"ディレクトリを作成します: {dir_path}")
                        os.makedirs(dir_path, exist_ok=True)

                    # 拡張子を取得
                    extension = os.path.splitext(file_name)[1].lower()
                    is_msg_file = extension == ".msg"

                    # .msgファイル以外のみattachmentフォルダに保存
                    if not is_msg_file:
                        # 添付ファイルを保存
                        self.logger.info(f"添付ファイルを保存します: {file_path}")
                        try:
                            attachment.SaveAsFile(file_path)
                            self.logger.info(
                                f"SaveAsFileメソッドの呼び出しが完了しました"
                            )
                        except Exception as save_error:
                            self.logger.error(
                                f"SaveAsFileで例外が発生: {str(save_error)}"
                            )
                            raise save_error

                        # ファイルが実際に作成されたか確認
                        if not os.path.exists(file_path):
                            self.logger.error(
                                f"添付ファイルの保存に失敗: {file_path} - ファイルが作成されませんでした"
                            )
                            continue

                        # ファイルサイズが0でないか確認
                        file_size = os.path.getsize(file_path)
                        if file_size == 0:
                            self.logger.warning(
                                f"添付ファイルのサイズが0です: {file_path}"
                            )
                    else:
                        # .msg形式の添付ファイルの場合は一時ディレクトリに直接保存
                        self.logger.info(f"添付ファイルの拡張子: {extension}")
                        self.logger.info(f"MSG形式の添付ファイルを処理します")

                        # 一時ディレクトリの作成
                        import tempfile

                        temp_dir = tempfile.mkdtemp()
                        self.logger.info(f"一時ディレクトリを作成しました: {temp_dir}")

                        # 一時ファイルパスを絶対パスで生成
                        temp_msg_path = os.path.abspath(
                            os.path.join(temp_dir, file_name)
                        )
                        self.logger.info(f"一時ファイルパス: {temp_msg_path}")

                        # 一時ファイルに直接保存
                        try:
                            attachment.SaveAsFile(temp_msg_path)
                            self.logger.info(
                                f"MSGファイルを一時ディレクトリに直接保存しました: {temp_msg_path}"
                            )

                            # ファイルが実際に作成されたか確認
                            if not os.path.exists(temp_msg_path):
                                self.logger.error(
                                    f"一時MSGファイルの保存に失敗: {temp_msg_path}"
                                )
                                continue

                            # ファイルサイズを取得
                            file_size = os.path.getsize(temp_msg_path)
                            if file_size == 0:
                                self.logger.warning(
                                    f"一時MSGファイルのサイズが0です: {temp_msg_path}"
                                )
                                continue
                        except Exception as save_error:
                            self.logger.error(
                                f"MSGファイルの一時保存で例外が発生: {str(save_error)}"
                            )
                            # 一時ディレクトリを削除して次へ
                            try:
                                import shutil

                                shutil.rmtree(temp_dir)
                                self.logger.info(
                                    f"一時ディレクトリを削除しました: {temp_dir}"
                                )
                            except Exception as e:
                                self.logger.warning(
                                    f"一時ディレクトリの削除に失敗: {str(e)}"
                                )
                            continue

                    # .msg形式の添付ファイルの場合、メールアイテムとして処理
                    self.logger.info(f"添付ファイルの拡張子: {extension}")

                    # .msgファイル処理のフラグ
                    is_msg_file = False

                    if extension == ".msg":
                        is_msg_file = True
                        self.logger.info(
                            f"MSG形式の添付ファイルを処理します: {temp_msg_path}"
                        )

                        try:
                            # MSG形式のファイルを一時的な場所からOutlookアイテムとして読み込む
                            try:
                                msg_item = outlook_service.get_item_from_msg(
                                    temp_msg_path
                                )
                                self.logger.info(
                                    f"MSGファイルをOutlookアイテムとして読み込みました"
                                )

                                # MSG復元アイテムのデバッグ出力を追加
                                self.logger.info(
                                    "MSGファイルから復元したメールアイテムのプロパティを調査します"
                                )

                                # object_util.pyのデバッグ関数を呼び出す
                                from src.util.object_util import (
                                    debug_print_mail_item,
                                    debug_print_mail_methods,
                                )

                                debug_print_mail_item(
                                    msg_item,
                                    "MSGファイルから復元したメールアイテムのプロパティ",
                                )
                                debug_print_mail_methods(
                                    msg_item,
                                    "MSGファイルから復元したメールアイテムのメソッド",
                                )

                                # EntryIDプロパティの存在を確認
                                from src.util.object_util import has_property

                                has_entry_id = has_property(msg_item, "EntryID")
                                self.logger.info(
                                    f"復元したアイテムにEntryIDプロパティが存在するか: {has_entry_id}"
                                )

                                # EntryIDを取得（直接アクセスを試みる）
                                entry_id = None
                                try:
                                    # COMオブジェクトは通常のPythonオブジェクトと異なる動作をするため
                                    # hasattr()でfalseを返してもgetattr()で値を取得できる場合がある
                                    entry_id = getattr(msg_item, "EntryID", None)
                                    if entry_id:
                                        self.logger.info(
                                            f"復元したメールからEntryIDを直接取得: {entry_id}"
                                        )
                                except Exception as attr_error:
                                    self.logger.warning(
                                        f"EntryID直接取得に失敗: {str(attr_error)}"
                                    )

                            except Exception as msg_error:
                                self.logger.error(
                                    f"MSGファイルの読み込みに失敗: {str(msg_error)}"
                                )
                                raise msg_error

                            if not msg_item:
                                self.logger.error(
                                    f"MSG形式のファイルの読み込みに失敗しました: {temp_msg_path}"
                                )
                                raise ValueError("MSGアイテムの取得に失敗しました")

                            # メールデータの構築
                            # 送受信時間の取得と変換
                            sent_time = get_safe(msg_item, "SentOn")
                            received_time = get_safe(msg_item, "ReceivedTime")

                            # datetime形式を文字列に変換
                            sent_time_str = self._format_date_string(sent_time)
                            received_time_str = self._format_date_string(received_time)

                            # フォルダ名を取得
                            folder_name = ""
                            try:
                                folder_query = """
                                SELECT name FROM outlook_snapshot
                                WHERE entry_id = ?
                                """
                                folder_result = self.items_db.execute_query(
                                    folder_query, (mail_data["folder_id"],)
                                )
                                if folder_result:
                                    folder_name = folder_result[0].get("name", "")
                            except Exception as e:
                                self.logger.error(f"フォルダ名の取得に失敗: {str(e)}")
                                folder_name = "不明"

                            # ConversationIDを取得
                            conversation_id = get_safe(msg_item, "ConversationID", "")

                            # 直接取得したEntryIDを優先して使用
                            msg_entry_id = (
                                entry_id
                                if entry_id
                                else f"{mail_id}_MSG_{uuid.uuid4()}"
                            )

                            # MSG添付メールデータの構築
                            msg_mail_data = {
                                "entry_id": msg_entry_id,
                                "store_id": get_safe(msg_item, "StoreID", ""),
                                "folder_id": mail_data[
                                    "folder_id"
                                ],  # 親メールと同じフォルダIDを使用
                                "conversation_id": conversation_id,
                                "message_type": "msg",  # .msg形式を示す
                                "parent_entry_id": mail_id,  # 親メールのentry_id
                                "parent_folder_name": folder_name,  # 親メールのフォルダ名
                                "subject": get_safe(msg_item, "Subject", ""),
                                "sent_time": sent_time_str,
                                "received_time": received_time_str,
                                "body": get_safe(msg_item, "Body", ""),
                                "html_body": get_safe(msg_item, "HTMLBody", ""),
                                "unread": get_safe(msg_item, "UnRead", 0),
                                "size": get_safe(msg_item, "Size", 0),
                                "has_attachments": get_safe(
                                    msg_item, "Attachments.Count", 0
                                )
                                > 0,
                                "attachment_count": get_safe(
                                    msg_item, "Attachments.Count", 0
                                ),
                                "task_id": self.task_id,  # タスクIDを追加
                                # 元のMSGファイルへのパスは保存しない
                                # "original_msg_path": file_path,
                            }

                            # 参加者情報の抽出
                            msg_mail_data["participants"] = self._extract_participants(
                                msg_item
                            )

                            # MSGメールの保存
                            msg_save_result = self._save_mail_item(msg_mail_data)
                            if msg_save_result:
                                self.logger.info(
                                    f"MSG形式のメールをDBに保存しました: {file_name}"
                                )

                                # MSG内の添付ファイルも即時処理する（メールオブジェクトが生きている間に）
                                if msg_mail_data["has_attachments"]:
                                    # 再帰的に添付ファイルを処理
                                    self.logger.info(
                                        f"MSG内の添付ファイルを再帰的に処理します"
                                    )
                                    msg_attachment_result = (
                                        self._process_attachment_for_mail(msg_mail_data)
                                    )
                                    self.logger.info(
                                        f"MSG内の添付ファイル処理結果: {msg_attachment_result}"
                                    )

                                    # 添付ファイル処理を完了としてマーク
                                    # メールIDを取得
                                    msg_mail_id = msg_mail_data["entry_id"]
                                    if msg_mail_id:
                                        # データベース内のメールタスクを検索
                                        task_query = """
                                        SELECT id FROM mail_tasks
                                        WHERE message_id = ? OR mail_id = ?
                                        """
                                        task_result = self.items_db.execute_query(
                                            task_query, (msg_mail_id, msg_mail_id)
                                        )

                                        if task_result:
                                            task_id = task_result[0]["id"]
                                            # 添付ファイル処理ステータスを成功に更新
                                            self._update_mail_task_status(
                                                task_id,
                                                "processing",  # 全体のステータスは「処理中」のまま
                                                attachment_status="success",  # 添付ファイル処理は「成功」
                                            )
                                            self.logger.info(
                                                f"MSG形式メール {msg_mail_id} の添付ファイル処理ステータスを成功としてマークしました"
                                            )

                                self.logger.info(
                                    f"MSG形式のメールの処理が完了しました: {file_name}"
                                )
                                processed_count += 1
                            else:
                                self.logger.error(
                                    f"MSG形式のメールの保存に失敗: {file_name}"
                                )

                        except Exception as e:
                            self.logger.error(
                                f"MSG形式のメール処理中にエラー: {str(e)}"
                            )
                        finally:
                            # 一時ディレクトリの削除
                            try:
                                import shutil

                                shutil.rmtree(temp_dir)
                                self.logger.info(
                                    f"一時ディレクトリを削除しました: {temp_dir}"
                                )
                            except Exception as e:
                                self.logger.warning(
                                    f"一時ディレクトリの削除に失敗: {str(e)}"
                                )

                        # MSGファイルは処理完了後にDBに情報登録しないためcontinueする
                        continue

                    # .msgファイルでない場合のみデータベースに添付ファイル情報を登録
                    query = """
                    INSERT INTO attachments (mail_id, name, path, type)
                    VALUES (?, ?, ?, ?)
                    """
                    self.items_db.execute_update(
                        query,
                        (
                            mail_id,
                            file_name,
                            file_path,
                            os.path.splitext(file_name)[1].lower().replace(".", ""),
                        ),
                    )
                    self.logger.info(f"添付ファイル情報をDBに登録しました: {file_name}")

                    processed_count += 1
                    self.logger.info(
                        f"添付ファイルを保存しました: {file_path}, サイズ: {file_size}バイト"
                    )

                except Exception as e:
                    self.logger.error(
                        f"添付ファイルの保存に失敗: {j}番目の添付ファイル, エラー: {str(e)}"
                    )
                    # 個別の添付ファイルのエラーはスキップし、次の添付ファイル処理を続行

            # メールタスクの取得とタスクステータスの更新
            task_query = """
            SELECT id FROM mail_tasks
            WHERE message_id = ? AND task_id = ?
            """
            task_result = self.items_db.execute_query(
                task_query, (mail_id, self.task_id)
            )

            if task_result:
                task_id = task_result[0]["id"]
                attachment_status = "success" if processed_count > 0 else "error"
                self._update_mail_task_status(
                    task_id, "processing", attachment_status=attachment_status
                )

            # 実際に処理した添付ファイルの数がデータベースに保存されている数と異なる場合は更新
            if processed_count != mail_data.get("attachment_count", 0):
                update_query = """
                UPDATE mail_items 
                SET attachment_count = ?
                WHERE entry_id = ?
                """
                self.items_db.execute_update(update_query, (processed_count, mail_id))
                self.logger.info(
                    f"添付ファイル数を更新しました: {mail_data.get('subject', 'Unknown')} ({processed_count}個)"
                )

            self.logger.info(
                f"添付ファイル処理完了: {processed_count}個のファイルを保存"
            )
            return processed_count > 0 or attachments.Count == 0

        except Exception as e:
            self.logger.error(f"添付ファイル処理でエラーが発生: {str(e)}")
            return False

    def _extract_mail_content(self, entry_id: str) -> Optional[dict]:
        """
        メールコンテンツの抽出

        Args:
            entry_id: メールのEntryID

        Returns:
            Optional[dict]: メールデータ辞書、取得失敗時はNone
        """
        try:
            # OutlookServiceを使用してメールアイテムを取得
            outlook_service = OutlookService()
            mail_item = outlook_service.get_item_by_id(entry_id)

            if not mail_item:
                self.logger.error(f"メールアイテムの取得に失敗: {entry_id}")
                return None

            # 送受信時間の取得と変換
            sent_time = get_safe(mail_item, "SentOn")
            received_time = get_safe(mail_item, "ReceivedTime")

            # 共通関数を使用して日時を文字列に変換
            sent_time_str = self._format_date_string(sent_time)
            received_time_str = self._format_date_string(received_time)

            # ConversationIDを取得（Exchange環境でのみ利用可能）
            conversation_id = get_safe(mail_item, "ConversationID", "")

            # 添付ファイル情報を取得
            has_attachments = False
            attachment_count = 0
            if hasattr(mail_item, "Attachments"):
                attachments = mail_item.Attachments
                if attachments and attachments.Count > 0:
                    has_attachments = True
                    attachment_count = attachments.Count

            # 基本メールデータの構築
            mail_data = {
                "entry_id": entry_id,
                "store_id": get_safe(mail_item, "StoreID", ""),
                "folder_id": get_safe(mail_item.Parent, "EntryID", ""),
                "conversation_id": conversation_id,
                "message_type": "email",  # デフォルトはemail
                "subject": self._clean_unicode_text(get_safe(mail_item, "Subject", "")),
                "sent_time": sent_time_str,
                "received_time": received_time_str,
                "body": self._clean_unicode_text(get_safe(mail_item, "Body", "")),
                "html_body": self._clean_unicode_text(
                    get_safe(mail_item, "HTMLBody", "")
                ),
                "unread": get_safe(mail_item, "UnRead", 0),
                "size": get_safe(mail_item, "Size", 0),
                "has_attachments": has_attachments,
                "attachment_count": attachment_count,
            }

            # 参加者情報の抽出
            mail_data["participants"] = self._extract_participants(mail_item)

            # 特殊なメッセージタイプの処理
            mail_data = self._update_message_type(mail_data)

            self.logger.info(f"メールコンテンツを抽出しました: {mail_data['subject']}")
            return mail_data

        except Exception as e:
            self.logger.error(f"メールコンテンツの抽出に失敗: {str(e)}")
            return None

    def _update_message_type(self, mail_data: dict) -> dict:
        """
        メールタイプの更新処理

        Args:
            mail_data: メールデータ

        Returns:
            dict: 更新されたメールデータ
        """
        if not mail_data:
            return mail_data

        try:
            # メールの件名にGUARDIANWALLが含まれている場合の処理
            subject = mail_data.get("subject", "")
            if "GUARDIANWALL" in subject:
                # データベース制約に合わせる
                mail_data["message_type"] = "guardian"
                # process_typeはNULLのままにする
                self.logger.info(f"メールタイプを'guardian'に更新しました: {subject}")

            return mail_data
        except Exception as e:
            self.logger.error(f"メールタイプの更新処理でエラーが発生: {str(e)}")
            return mail_data

    def _save_mail_item(self, mail_data: dict) -> bool:
        """
        メールアイテムの保存

        Args:
            mail_data: 保存するメールのデータ

        Returns:
            bool: 保存が成功したかどうか
        """
        if not mail_data:
            self.logger.error("保存するメールデータがありません")
            return False

        try:
            # 必須フィールドのチェック
            required_fields = [
                "entry_id",
                "folder_id",
                "subject",
                "sent_time",
                "received_time",
            ]
            for field in required_fields:
                if not mail_data.get(field):
                    self.logger.error(f"必須フィールド '{field}' の値がありません")
                    return False

            # 日時形式の検証 - 形式が「YYYY-MM-DD HH:MM:SS」、長さが19文字であることを確認
            date_fields = ["sent_time", "received_time"]
            for field in date_fields:
                value = mail_data.get(field, "")
                if (
                    len(value) != 19
                    or not value.replace("-", "")
                    .replace(" ", "")
                    .replace(":", "")
                    .isdigit()
                ):
                    self.logger.error(f"フィールド '{field}' の日時形式が不正: {value}")
                    return False

            # HTMLコンテンツをMarkdown形式に変換（一時的に無効化）
            # html_content = mail_data.get("html_body", "")
            # markdown_content = ""
            # if html_content:
            #     try:
            #         # HTMLコンテンツをMarkdown形式に変換
            #         markdown_content = markdownify(html_content)
            #         self.logger.info(f"HTMLコンテンツをMarkdown形式に変換しました: {mail_data['subject']}")
            #     except Exception as e:
            #         self.logger.error(f"Markdown変換エラー: {str(e)}")
            #         # 変換エラーの場合はMarkdownとして処理しない
            #         markdown_content = ""

            # トランザクション開始
            self.items_db.begin_transaction()

            try:
                # まず参加者情報を保存
                participant_ids = self._save_participants(
                    mail_data["entry_id"], mail_data["participants"]
                )

                # mail_itemsテーブルにメールデータを保存
                query = """
                INSERT INTO mail_items (
                    entry_id, store_id, folder_id, conversation_id, 
                    message_type, subject, sent_time, received_time,
                    body, unread, message_size, task_id, has_attachments, attachment_count, processed_at
                """

                # process_typeがある場合は追加
                if mail_data.get("process_type"):
                    query += ", process_type"

                query += ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now')"

                # process_typeがある場合はパラメーターにプレースホルダーを追加
                if mail_data.get("process_type"):
                    query += ", ?"

                query += ")"

                # 現在の時刻を取得
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 添付ファイルの個数を取得 - raw_itemは使用せず、直接mail_dataから取得
                attachment_count = mail_data.get("attachment_count", 0)

                params = [
                    mail_data["entry_id"],
                    mail_data["store_id"],
                    mail_data["folder_id"],
                    mail_data["conversation_id"],
                    mail_data["message_type"],
                    mail_data["subject"],
                    mail_data["sent_time"],
                    mail_data["received_time"],
                    mail_data["body"],
                    mail_data["unread"],
                    mail_data["size"],
                    self.task_id,
                    (
                        1 if mail_data.get("has_attachments") else 0
                    ),  # has_attachments (0=なし、1=あり)
                    attachment_count,  # 添付ファイルの個数
                ]

                # process_typeがある場合はパラメータに追加
                if mail_data.get("process_type"):
                    params.append(mail_data["process_type"])

                # メールデータを保存
                self.items_db.execute_update(query, tuple(params))

                # Markdown化されたHTMLコンテンツをstyled_bodyテーブルに保存（一時的に無効化）
                # if markdown_content:
                #     styled_body_query = """
                #     INSERT OR REPLACE INTO styled_body (
                #         entry_id, styled_body, keywords
                #     ) VALUES (?, ?, ?)
                #     """
                #
                #     # キーワードは現時点では空文字列で保存
                #     styled_body_params = (
                #         mail_data["entry_id"],
                #         markdown_content,
                #         "",  # キーワード（今後の拡張用）
                #     )
                #
                #     self.items_db.execute_update(styled_body_query, styled_body_params)
                #     self.logger.info(f"Markdown化されたコンテンツをstyled_bodyテーブルに保存しました: {mail_data['subject']}")

                # mail_tasksテーブルの状態を更新
                # message_idからtask idを取得
                task_query = """
                SELECT id FROM mail_tasks
                WHERE message_id = ? AND task_id = ?
                """
                task_result = self.items_db.execute_query(
                    task_query, (mail_data["entry_id"], self.task_id)
                )

                if task_result:
                    task_id = task_result[0]["id"]

                    # タスクのstatusとmail_fetch_statusを更新
                    self._update_mail_task_status(
                        task_id, "processing", mail_fetch_status="success"
                    )

                # コミット
                self.items_db.commit()
                self.logger.info(
                    f"メールデータをDBに保存しました: {mail_data['subject']}"
                )
                return True

            except Exception as e:
                # ロールバック
                self.items_db.rollback()
                self.logger.error(f"メールデータ保存中のSQLエラー: {str(e)}")
                raise e

        except Exception as e:
            self.logger.error(f"メールデータの保存に失敗: {str(e)}")
            return False

    def _save_participants(self, mail_id: str, participants: dict) -> dict:
        """
        参加者情報をデータベースに保存する

        Args:
            mail_id: メールID
            participants: 参加者情報

        Returns:
            dict: 参加者タイプごとのユーザーID辞書
        """
        participant_ids = {"sender": [], "to": [], "cc": [], "bcc": []}

        try:
            # 現在時刻
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 送信者の処理
            for sender in participants.get("sender", []):
                if not sender.get("email"):
                    continue

                # ユーザー情報の保存/更新
                user_id = self._save_user_info(sender, current_time)
                if user_id:
                    # participantsテーブルに関連を保存
                    self._save_participant_relation(
                        mail_id, user_id, "sender", current_time
                    )
                    participant_ids["sender"].append(user_id)

            # 受信者の処理
            for recipient_type in ["to", "cc", "bcc"]:
                for recipient in participants.get(recipient_type, []):
                    if not recipient.get("email"):
                        continue

                    # ユーザー情報の保存/更新
                    user_id = self._save_user_info(recipient, current_time)
                    if user_id:
                        # participantsテーブルに関連を保存
                        self._save_participant_relation(
                            mail_id, user_id, recipient_type, current_time
                        )
                        participant_ids[recipient_type].append(user_id)

            return participant_ids

        except Exception as e:
            self.logger.error(f"参加者情報の保存に失敗: {str(e)}")
            return participant_ids

    def _save_user_info(self, user_info: dict, timestamp: str) -> int:
        """
        ユーザー情報を保存/更新する

        Args:
            user_info: ユーザー情報
            timestamp: タイムスタンプ

        Returns:
            int: ユーザーID
        """
        try:
            email = user_info.get("email", "")
            if not email:
                return None

            # 既存ユーザーのチェック
            check_query = "SELECT id FROM users WHERE email = ?"
            result = self.items_db.execute_query(check_query, (email,))

            if result:
                # 既存ユーザーの更新
                user_id = result[0]["id"]

                update_query = """
                UPDATE users SET 
                    name = ?,
                    display_name = ?,
                    company = ?,
                    office_location = ?,
                    smtp_address = ?,
                    updated_at = ?
                WHERE id = ?
                """

                self.items_db.execute_update(
                    update_query,
                    (
                        user_info.get("name", user_info.get("display_name", "")),
                        user_info.get("display_name", ""),
                        user_info.get("company", ""),
                        user_info.get("office_location", ""),
                        user_info.get("smtp_address", email),
                        timestamp,
                        user_id,
                    ),
                )

                return user_id
            else:
                # 新規ユーザーの作成
                insert_query = """
                INSERT INTO users (
                    email, name, display_name, company, office_location, smtp_address,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """

                self.items_db.execute_update(
                    insert_query,
                    (
                        email,
                        user_info.get("name", user_info.get("display_name", "")),
                        user_info.get("display_name", ""),
                        user_info.get("company", ""),
                        user_info.get("office_location", ""),
                        user_info.get("smtp_address", email),
                        timestamp,
                        timestamp,
                    ),
                )

                # 新しく挿入されたユーザーIDを取得
                id_query = "SELECT id FROM users WHERE email = ?"
                result = self.items_db.execute_query(id_query, (email,))

                if result:
                    return result[0]["id"]

                return None

        except Exception as e:
            self.logger.error(f"ユーザー情報の保存に失敗: {str(e)}")
            return None

    def _save_participant_relation(
        self, mail_id: str, user_id: int, participant_type: str, timestamp: str
    ) -> bool:
        """
        メールと参加者の関連を保存する

        Args:
            mail_id: メールID
            user_id: ユーザーID
            participant_type: 参加者タイプ (sender, to, cc, bcc)
            timestamp: タイムスタンプ

        Returns:
            bool: 保存が成功したかどうか
        """
        try:
            # 既存の関連をチェック
            check_query = """
            SELECT id FROM participants 
            WHERE mail_id = ? AND user_id = ? AND participant_type = ?
            """
            result = self.items_db.execute_query(
                check_query, (mail_id, user_id, participant_type)
            )

            if not result:
                # 新規関連の保存
                insert_query = """
                INSERT INTO participants (
                    mail_id, user_id, participant_type, address_type
                ) VALUES (?, ?, ?, 'SMTP')
                """

                self.items_db.execute_update(
                    insert_query, (mail_id, user_id, participant_type)
                )

            return True

        except Exception as e:
            self.logger.error(f"参加者関連の保存に失敗: {str(e)}")
            return False

    def _process_ai_review(self, mail_id: str) -> bool:
        """
        AIレビューの処理

        Args:
            mail_id: メールID

        Returns:
            bool: 処理が成功したかどうか
        """
        try:
            # メールデータを取得
            mail_query = """
            SELECT 
                entry_id, subject, body, sent_time, received_time,
                has_attachments, conversation_id
            FROM mail_items 
            WHERE entry_id = ?
            """
            mail_result = self.items_db.execute_query(mail_query, (mail_id,))

            if not mail_result:
                self.logger.error(
                    f"AIレビュー: メールデータが見つかりません: {mail_id}"
                )
                return False

            mail_data = mail_result[0]

            # 会話IDを取得（必須）
            conversation_id = mail_data.get("conversation_id")
            if not conversation_id:
                self.logger.error(f"AIレビュー: 会話IDが見つかりません: {mail_id}")
                return False

            # 参加者情報を取得
            participants_query = """
            SELECT u.name, u.email, p.participant_type
            FROM participants p
            JOIN users u ON p.user_id = u.id
            WHERE p.mail_id = ?
            """
            participants_result = self.items_db.execute_query(
                participants_query, (mail_id,)
            )

            # AIに送信するデータを構築
            mail_info = {
                "subject": mail_data.get("subject", ""),
                "sent_time": mail_data.get("sent_time", ""),
                "received_time": mail_data.get("received_time", ""),
                "body": mail_data.get("body", ""),
                "has_attachments": bool(mail_data.get("has_attachments", 0)),
                "participants": {"sender": [], "to": [], "cc": [], "bcc": []},
            }

            # 参加者情報を整理
            for p in participants_result:
                p_type = p.get("participant_type", "")
                if p_type in ["sender", "to", "cc", "bcc"]:
                    mail_info["participants"][p_type].append(
                        {"name": p.get("name", ""), "email": p.get("email", "")}
                    )

            # AIReviewクラスを初期化して非同期処理を実行
            import asyncio

            from src.models.azure.ai_review import AIReview

            # AIレビュー用のプロンプトを構築
            prompt_data = {
                "mail_id": mail_id[:8] + "...",  # IDは短縮して表示
                "conversation_id": conversation_id[:8] + "...",  # 会話IDも短縮
                "subject": mail_info["subject"],
                "body": mail_info["body"],
                "sender": mail_info["participants"]["sender"],
                "recipients": {
                    "to": mail_info["participants"]["to"],
                    "cc": mail_info["participants"]["cc"],
                    "bcc": mail_info["participants"]["bcc"],
                },
                "sent_time": mail_info["sent_time"],
                "has_attachments": mail_info["has_attachments"],
            }

            # 非同期処理を実行するための関数
            async def run_ai_review():
                ai_review = AIReview()
                try:
                    # プロンプトをJSON文字列に変換
                    import json

                    prompt_json = json.dumps(prompt_data, ensure_ascii=False)

                    # AIクライアントとタスクマネージャーを初期化
                    from src.models.azure.openai_client import OpenAIClient
                    from src.models.azure.task_manager import TaskManager

                    # システムプロンプトを読み込む
                    system_prompt = "メールの内容を分析し、その概要、リスク評価、重要度を判断してください。"
                    try:
                        import os

                        prompt_path = os.path.join("config", "prompt.txt")
                        if os.path.exists(prompt_path):
                            with open(prompt_path, "r", encoding="utf-8") as f:
                                system_prompt = f.read().strip()
                    except Exception as e:
                        self.logger.warning(
                            f"システムプロンプトの読み込みに失敗しました: {e}"
                        )

                    client = OpenAIClient(system_prompt=system_prompt)
                    manager = TaskManager(client)

                    # コールバック関数
                    result_data = None

                    async def callback(prompt_str, result):
                        nonlocal result_data
                        if result:
                            result_data = result

                    # AIに処理を依頼
                    await manager.execute_tasks([prompt_json], callback)

                    # 結果を返す
                    return result_data
                except Exception as e:
                    self.logger.error(f"AIレビュー実行中にエラーが発生しました: {e}")
                    return None

            # 非同期関数を実行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(run_ai_review())
            finally:
                loop.close()

            # AIの結果をデータベースに保存
            if result:
                # 新しい結果を保存（INSERT OR REPLACEを使用して既存のデータを上書き）
                self.items_db.execute_update(
                    """
                    INSERT OR REPLACE INTO ai_reviews (conversation_id, result)
                    VALUES (?, ?)
                    """,
                    (conversation_id, result),
                )

                self.logger.info(
                    f"AIレビュー結果を保存しました: 会話ID {conversation_id}"
                )
                return True
            else:
                self.logger.error(f"AIレビュー結果が取得できませんでした: {mail_id}")
                return False

        except Exception as e:
            self.logger.error(f"AIレビュー処理でエラーが発生: {str(e)}")
            return False

    def _extract_participants(self, mail_item):
        """
        メールの参加者情報を抽出する

        Args:
            mail_item: Outlookのメールアイテム

        Returns:
            dict: 参加者情報を含む辞書
        """
        participants = {"sender": [], "to": [], "cc": [], "bcc": []}

        try:
            # 送信者情報の抽出
            sender = mail_item.Sender
            if sender:
                try:
                    # SenderのAddressEntryを取得
                    address_entry = sender.AddressEntry
                    if address_entry:
                        sender_info = {
                            "display_name": get_safe(sender, "Name"),
                            "email": get_safe(address_entry, "Address", ""),
                            "type": "sender",
                        }

                        # AddressEntryオブジェクトから詳細情報を取得
                        if hasattr(address_entry, "GetExchangeUser"):
                            exchange_user = address_entry.GetExchangeUser()
                            if exchange_user:
                                sender_info.update(
                                    {
                                        "name": get_safe(
                                            exchange_user,
                                            "Name",
                                            sender_info["display_name"],
                                        ),
                                        "company": get_safe(
                                            exchange_user, "CompanyName", ""
                                        ),
                                        "office_location": get_safe(
                                            exchange_user, "OfficeLocation", ""
                                        ),
                                        "smtp_address": get_safe(
                                            exchange_user,
                                            "PrimarySmtpAddress",
                                            sender_info["email"],
                                        ),
                                    }
                                )

                        # 表示名が空の場合はメールアドレスで代替
                        if not sender_info["display_name"] and sender_info.get("email"):
                            sender_info["display_name"] = sender_info["email"]

                        # 名前が空の場合は表示名で代替
                        if not sender_info.get("name") and sender_info["display_name"]:
                            sender_info["name"] = sender_info["display_name"]

                        participants["sender"].append(sender_info)
                except Exception as e:
                    self.logger.warning(f"送信者の詳細情報取得に失敗: {e}")
                    # 基本情報だけ追加
                    participants["sender"].append(
                        {
                            "display_name": get_safe(sender, "Name", "不明な送信者"),
                            "email": get_safe(sender, "Address", ""),
                            "type": "sender",
                            "name": get_safe(sender, "Name", "不明な送信者"),
                        }
                    )

            # 受信者情報の抽出
            if hasattr(mail_item, "Recipients") and mail_item.Recipients:
                for i in range(1, mail_item.Recipients.Count + 1):
                    try:
                        recipient = mail_item.Recipients.Item(i)
                        recipient_type = get_safe(recipient, "Type", 0)

                        # 受信者タイプによって分類 (0=To, 1=CC, 2=BCC)
                        type_map = {1: "to", 2: "cc", 3: "bcc", 0: "originator"}
                        recipient_category = type_map.get(recipient_type, "to")

                        recipient_info = {
                            "display_name": get_safe(recipient, "Name", ""),
                            "email": get_safe(recipient, "Address", ""),
                            "type": recipient_category,
                        }

                        # AddressEntryオブジェクトから詳細情報を取得
                        address_entry = get_safe(recipient, "AddressEntry")
                        if address_entry:
                            # メールアドレスをAddressEntryから取得
                            if (
                                hasattr(address_entry, "Address")
                                and not recipient_info["email"]
                            ):
                                recipient_info["email"] = get_safe(
                                    address_entry, "Address", ""
                                )

                            # ExchangeUserからより詳細な情報を取得
                            if hasattr(address_entry, "GetExchangeUser"):
                                try:
                                    exchange_user = address_entry.GetExchangeUser()
                                    if exchange_user:
                                        recipient_info.update(
                                            {
                                                "name": get_safe(
                                                    exchange_user,
                                                    "Name",
                                                    recipient_info["display_name"],
                                                ),
                                                "company": get_safe(
                                                    exchange_user, "CompanyName", ""
                                                ),
                                                "office_location": get_safe(
                                                    exchange_user, "OfficeLocation", ""
                                                ),
                                                "smtp_address": get_safe(
                                                    exchange_user,
                                                    "PrimarySmtpAddress",
                                                    recipient_info["email"],
                                                ),
                                            }
                                        )
                                except Exception as e:
                                    self.logger.warning(
                                        f"受信者のExchangeUser取得に失敗: {e}"
                                    )

                        # 表示名が空の場合はメールアドレスで代替
                        if (
                            not recipient_info["display_name"]
                            and recipient_info["email"]
                        ):
                            recipient_info["display_name"] = recipient_info["email"]

                        # 名前が空の場合は表示名で代替
                        if (
                            not recipient_info.get("name")
                            and recipient_info["display_name"]
                        ):
                            recipient_info["name"] = recipient_info["display_name"]

                        participants[recipient_category].append(recipient_info)
                    except Exception as e:
                        self.logger.warning(f"受信者情報の処理に失敗: {e}")

        except Exception as e:
            self.logger.error(f"参加者情報の抽出に失敗: {e}")

        return participants

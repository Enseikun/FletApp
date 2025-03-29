import os
import shutil
import time
from typing import Any, Dict, List, Optional, Tuple

from src.core.database import DatabaseManager
from src.core.logger import get_logger
from src.models.outlook.mail_processing_manager import MailProcessingManager
from src.models.outlook.outlook_item_model import OutlookItemModel
from src.util.object_util import get_safe


class HomeContentModel:
    """
    ホーム画面のコンテンツ用モデル
    tasks.dbからデータを取得・操作する
    """

    def __init__(self, db_path: str = None):
        """初期化"""
        self.logger = get_logger()

        # デフォルトのデータベースパスを設定
        if db_path is None:
            # プロジェクトのルートディレクトリを基準にデータベースパスを設定
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data",
                "tasks.db",
            )
            self.logger.debug(
                "HomeContentModel: デフォルトデータベースパス設定", db_path=db_path
            )
        else:
            self.logger.debug(
                "HomeContentModel: 指定されたデータベースパス使用", db_path=db_path
            )

        self.db_manager = DatabaseManager(db_path)
        self.logger.info("HomeContentModel: 初期化完了", db_path=db_path)

    def create_task_directory_and_database(self, task_id: str) -> bool:
        """
        タスクフォルダとデータベースを作成する

        Args:
            task_id: タスクID

        Returns:
            bool: 作成が成功したかどうか
        """
        try:
            # タスクフォルダのパスを設定
            task_dir = os.path.join("data", "tasks", str(task_id))

            # フォルダが存在しない場合のみ作成
            if not os.path.exists(task_dir):
                os.makedirs(task_dir)
                self.logger.info(
                    f"HomeContentModel: タスクフォルダを作成しました - {task_dir}"
                )

            # items.dbのパスを設定
            items_db_path = os.path.join(task_dir, "items.db")

            # items.dbが存在しない場合のみ作成
            if not os.path.exists(items_db_path):
                # データベースを作成
                db_manager = DatabaseManager(items_db_path)

                # 外部キー制約を一時的に無効化
                db_manager.execute_update("PRAGMA foreign_keys = OFF")

                # items.sqlの内容を読み込んで実行
                sql_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    "data",
                    "items.sql",
                )
                with open(sql_path, "r", encoding="utf-8") as f:
                    sql_script = f.read()

                # SQLスクリプトを実行
                db_manager.execute_script(sql_script)
                db_manager.commit()

                # 外部キー制約を再度有効化
                db_manager.execute_update("PRAGMA foreign_keys = ON")
                db_manager.commit()

                db_manager.disconnect()

                self.logger.info(
                    f"HomeContentModel: items.dbを作成し、スキーマを適用しました - {items_db_path}"
                )

            return True
        except Exception as e:
            self.logger.error(
                f"HomeContentModel: タスクフォルダまたはデータベースの作成に失敗しました - {e}"
            )
            return False

    def get_tasks_data(self) -> List[Tuple[int, str]]:
        """
        tasks.dbからタスクデータを取得する

        Returns:
            List[Tuple[int, str]]: (id, from_folder_name)のリスト
        """
        try:
            self.logger.debug("HomeContentModel: タスクデータ取得開始")
            # DatabaseManagerを使用してクエリを実行
            query = "SELECT id, from_folder_name FROM task_info"
            results = self.db_manager.execute_query(query)

            # 辞書のリストをタプルのリストに変換
            task_data = [
                (get_safe(item, "id"), get_safe(item, "from_folder_name"))
                for item in results
            ]
            self.logger.info(
                "HomeContentModel: タスクデータ取得成功", task_count=len(task_data)
            )
            return task_data
        except Exception as e:
            self.logger.error("HomeContentModel: タスクデータ取得エラー", error=str(e))
            return []

    def delete_task(self, task_id: str) -> bool:
        """
        指定されたIDのタスクをデータベースから削除する

        Args:
            task_id: 削除するタスクのID

        Returns:
            bool: 削除が成功したかどうか
        """
        try:
            # データベース操作を先に完了
            self.db_manager.execute_update(
                "DELETE FROM task_info WHERE id = ?", (task_id,)
            )
            self.db_manager.commit()

            # データベース接続を確実に閉じる
            self.db_manager.disconnect()

            # ディレクトリ削除を試みる
            task_dir = os.path.join("data", "tasks", str(task_id))
            if os.path.exists(task_dir):
                try:
                    shutil.rmtree(task_dir)
                except PermissionError:
                    # ファイルが使用中の場合は少し待ってから再試行
                    time.sleep(0.1)
                    shutil.rmtree(task_dir)

            return True
        except Exception as e:
            self.logger.error(f"タスク削除エラー: {str(e)}")
            return False

    def create_outlook_snapshot(self, task_id: str) -> bool:
        """
        outlook.dbのfoldersテーブルの状態をitems.dbのoutlook_snapshotテーブルに記録する

        Args:
            task_id: タスクID

        Returns:
            bool: 記録が成功したかどうか
        """
        outlook_db = None
        items_db = None
        try:
            self.logger.info(
                "HomeContentModel: Outlookスナップショット作成開始", task_id=task_id
            )

            # outlook.dbのパスを設定
            outlook_db_path = os.path.join("data", "outlook.db")
            outlook_db = DatabaseManager(outlook_db_path)

            # items.dbのパスを設定
            items_db_path = os.path.join("data", "tasks", str(task_id), "items.db")
            items_db = DatabaseManager(items_db_path)

            # トランザクション開始
            items_db.execute_update("BEGIN TRANSACTION")
            outlook_db.execute_update("BEGIN TRANSACTION")

            try:
                # outlook.dbからfoldersテーブルのデータを取得
                folders_data = outlook_db.execute_query("SELECT * FROM folders")

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
                        get_safe(folder, "folder_type"),  # オプショナルなフィールド
                        get_safe(folder, "folder_class"),  # オプショナルなフィールド
                        get_safe(folder, "item_count"),
                        get_safe(folder, "unread_count"),
                    )
                    items_db.execute_update(query, params)

                # 抽出計画を記録
                success = self._create_extraction_plan(task_id, items_db, outlook_db)

                if success:
                    # トランザクションをコミット
                    items_db.execute_update("COMMIT")
                    outlook_db.execute_update("COMMIT")
                    self.logger.info(
                        "HomeContentModel: Outlookスナップショット作成成功",
                        task_id=task_id,
                    )
                else:
                    # 抽出計画作成失敗時はロールバック
                    items_db.execute_update("ROLLBACK")
                    outlook_db.execute_update("ROLLBACK")
                    self.logger.error(
                        "HomeContentModel: 抽出計画の作成に失敗しました",
                        task_id=task_id,
                    )

                return success

            except Exception as e:
                # エラー時はトランザクションをロールバック
                items_db.execute_update("ROLLBACK")
                outlook_db.execute_update("ROLLBACK")
                raise e

        except Exception as e:
            self.logger.error(
                "HomeContentModel: Outlookスナップショット作成エラー",
                task_id=task_id,
                error=str(e),
            )
            return False

        finally:
            # データベース接続を確実に閉じる
            if outlook_db:
                outlook_db.disconnect()
            if items_db:
                items_db.disconnect()

    def _create_extraction_plan(
        self, task_id: str, items_db: DatabaseManager, outlook_db: DatabaseManager
    ) -> bool:
        """
        メールアイテムの抽出計画を作成する

        Args:
            task_id: タスクID
            items_db: items.dbのDatabaseManagerインスタンス
            outlook_db: outlook.dbのDatabaseManagerインスタンス

        Returns:
            bool: 作成が成功したかどうか
        """
        try:
            self.logger.info("HomeContentModel: 抽出計画作成開始", task_id=task_id)

            # task_infoテーブルからタスク情報を取得
            task_info = outlook_db.execute_query(
                "SELECT * FROM task_info WHERE id = ?", (task_id,)
            )
            if not task_info:
                self.logger.error(
                    "HomeContentModel: タスク情報が見つかりません", task_id=task_id
                )
                return False

            task = task_info[0]
            from_folder_id = get_safe(task, "from_folder_id")
            from_folder_name = get_safe(task, "from_folder_name")
            start_date = get_safe(task, "start_date")
            end_date = get_safe(task, "end_date")
            exclude_extensions = get_safe(task, "exclude_extensions")

            # 対象フォルダのメールアイテムを取得
            mail_items_query = """
            SELECT entry_id, subject, sent_time, received_time
            FROM mail_items
            WHERE folder_id = ?
            AND sent_time BETWEEN ? AND ?
            ORDER BY sent_time ASC
            """
            mail_items = outlook_db.execute_query(
                mail_items_query, (from_folder_id, start_date, end_date)
            )
            total_messages = len(mail_items)

            if total_messages == 0:
                self.logger.warning(
                    "HomeContentModel: 対象メールがありません",
                    task_id=task_id,
                    from_folder=from_folder_name,
                    start_date=start_date,
                    end_date=end_date,
                )
                return False

            # 抽出条件を記録
            extraction_conditions_query = """
            INSERT INTO extraction_conditions (
                task_id, from_folder_id, from_folder_name,
                start_date, end_date, exclude_extensions,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """
            items_db.execute_update(
                extraction_conditions_query,
                (
                    task_id,
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
            for mail_item in mail_items:
                items_db.execute_update(
                    mail_tasks_query,
                    (
                        task_id,
                        get_safe(mail_item, "entry_id"),
                        get_safe(mail_item, "subject"),
                        get_safe(mail_item, "sent_time"),
                    ),
                )

            # task_progressテーブルに進捗状況を記録
            task_progress_query = """
            INSERT INTO task_progress (
                task_id, total_messages, processed_messages,
                successful_messages, failed_messages, skipped_messages,
                status, last_updated_at
            ) VALUES (?, ?, 0, 0, 0, 0, 'pending', datetime('now'))
            """
            items_db.execute_update(task_progress_query, (task_id, total_messages))

            self.logger.info(
                "HomeContentModel: 抽出計画作成成功",
                task_id=task_id,
                total_messages=total_messages,
                from_folder=from_folder_name,
                start_date=start_date,
                end_date=end_date,
            )
            return True

        except Exception as e:
            self.logger.error(
                "HomeContentModel: 抽出計画作成エラー", task_id=task_id, error=str(e)
            )
            return False

    def start_mail_extraction(self, task_id: str) -> bool:
        """
        メール抽出作業を開始する

        Args:
            task_id: タスクID

        Returns:
            bool: 開始が成功したかどうか
        """
        try:
            self.logger.info("HomeContentModel: メール抽出作業開始", task_id=task_id)

            # タスク情報の取得
            task_info = self._get_task_info(task_id)
            if not task_info:
                self.logger.error(
                    "HomeContentModel: タスク情報が見つかりません", task_id=task_id
                )
                return False

            # モデルの初期化
            outlook_model = OutlookItemModel()
            processing_manager = MailProcessingManager(outlook_model)

            # メールアイテムの取得と処理
            folder_id = get_safe(task_info, "from_folder_id")
            filter_criteria = self._build_filter_criteria(task_info)

            total_processed = 0
            for chunk in outlook_model.get_mail_items(folder_id, filter_criteria):
                # チャンク単位で処理
                with self.db_manager.get_connection() as conn:
                    success, results = processing_manager.process_chunk(chunk, conn)

                    if not success:
                        self.logger.error(
                            "HomeContentModel: チャンク処理に失敗",
                            task_id=task_id,
                            chunk_size=len(chunk),
                        )
                        return False

                    # 処理結果の保存
                    for result in results:
                        self._save_processing_results(conn, task_id, result)

                total_processed += len(chunk)
                self.logger.info(
                    "HomeContentModel: チャンク処理完了",
                    task_id=task_id,
                    processed=total_processed,
                )

                # 進捗状況の更新
                self._update_task_progress(task_id, total_processed)

            self.logger.info(
                "HomeContentModel: メール抽出作業完了",
                task_id=task_id,
                total_processed=total_processed,
            )
            return True

        except Exception as e:
            self.logger.error(
                "HomeContentModel: メール抽出作業エラー", task_id=task_id, error=str(e)
            )
            return False

    def _save_processing_results(
        self, conn, task_id: str, result: Dict[str, Any]
    ) -> None:
        """
        処理結果をデータベースに保存する

        Args:
            conn: データベース接続
            task_id: タスクID
            result: 処理結果
        """
        try:
            cursor = conn.cursor()
            mail_id = result["mail_id"]
            mail_info = result["mail_info"]

            # メール情報の保存
            cursor.execute(
                """
                INSERT OR REPLACE INTO mail_items (
                    entry_id, subject, received_time, sender_name,
                    unread, has_attachments, size, categories
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    mail_id,
                    mail_info["subject"],
                    mail_info["received_time"],
                    mail_info["sender_name"],
                    mail_info["unread"],
                    mail_info["has_attachments"],
                    mail_info["size"],
                    mail_info["categories"],
                ),
            )

            # 添付ファイル情報の保存
            for attachment in result["attachments"]:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO attachments (
                        mail_id, file_name, file_size, file_path
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        mail_id,
                        attachment["file_name"],
                        attachment["file_size"],
                        attachment["file_path"],
                    ),
                )

            # 参加者情報の保存
            for participant in result["participants"]:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO participants (
                        mail_id, email_address, display_name, participant_type
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        mail_id,
                        participant["email_address"],
                        participant["display_name"],
                        participant["participant_type"],
                    ),
                )

            # タスク進捗の更新
            cursor.execute(
                """
                UPDATE mail_tasks
                SET status = 'completed',
                    mail_fetch_status = 'completed',
                    attachment_status = 'completed',
                    updated_at = datetime('now')
                WHERE task_id = ? AND message_id = ?
                """,
                (task_id, mail_id),
            )

        except Exception as e:
            self.logger.error(f"処理結果の保存エラー: {e}")
            raise

    def _get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        タスク情報を取得する

        Args:
            task_id: タスクID

        Returns:
            Optional[Dict[str, Any]]: タスク情報
        """
        try:
            query = "SELECT * FROM task_info WHERE id = ?"
            results = self.db_manager.execute_query(query, (task_id,))
            return results[0] if results else None
        except Exception as e:
            self.logger.error(f"タスク情報の取得に失敗: {e}")
            return None

    def _build_filter_criteria(self, task_info: Dict[str, Any]) -> Optional[str]:
        """
        フィルタ条件を構築する

        Args:
            task_info: タスク情報

        Returns:
            Optional[str]: フィルタ条件
        """
        try:
            start_date = get_safe(task_info, "start_date")
            end_date = get_safe(task_info, "end_date")

            if not start_date or not end_date:
                return None

            return f"[Sent] >= '{start_date}' AND [Sent] <= '{end_date}'"
        except Exception as e:
            self.logger.error(f"フィルタ条件の構築に失敗: {e}")
            return None

    def _update_task_progress(self, task_id: str, processed_count: int) -> None:
        """
        タスクの進捗状況を更新する

        Args:
            task_id: タスクID
            processed_count: 処理済み件数
        """
        try:
            query = """
            UPDATE task_progress
            SET processed_messages = ?,
                last_updated_at = datetime('now')
            WHERE task_id = ?
            """
            self.db_manager.execute_update(query, (processed_count, task_id))
            self.db_manager.commit()
        except Exception as e:
            self.logger.error(f"進捗状況の更新に失敗: {e}")

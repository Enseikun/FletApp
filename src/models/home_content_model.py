import os
import shutil
import time
from typing import Any, Dict, List, Optional, Tuple

from src.core.database import DatabaseManager
from src.core.logger import get_logger
from src.models.outlook.outlook_extraction_service import OutlookExtractionService
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

    def check_snapshot_and_extraction_plan(self, task_id: str) -> Dict[str, bool]:
        """
        スナップショットと抽出計画の存在を確認する

        Args:
            task_id: タスクID

        Returns:
            Dict[str, bool]: スナップショットと抽出計画の存在状況
        """
        result = {
            "has_snapshot": False,
            "has_extraction_plan": False,
            "extraction_in_progress": False,
            "extraction_completed": False,
        }

        try:
            # items.dbに接続
            items_db_path = os.path.join("data", "tasks", str(task_id), "items.db")
            if not os.path.exists(items_db_path):
                self.logger.warning(
                    f"HomeContentModel: items.dbが見つかりません - {items_db_path}"
                )
                return result

            items_db = DatabaseManager(items_db_path)

            # スナップショットの存在確認
            snapshot_query = "SELECT COUNT(*) as count FROM outlook_snapshot"
            snapshot_result = items_db.execute_query(snapshot_query)
            if snapshot_result and snapshot_result[0].get("count", 0) > 0:
                result["has_snapshot"] = True

            # 抽出計画の存在確認
            plan_query = "SELECT COUNT(*) as count FROM mail_tasks WHERE task_id = ?"
            plan_result = items_db.execute_query(plan_query, (task_id,))
            if plan_result and plan_result[0].get("count", 0) > 0:
                result["has_extraction_plan"] = True

            # 抽出進捗の確認
            progress_query = """
            SELECT status FROM task_progress 
            WHERE task_id = ? 
            ORDER BY last_updated_at DESC LIMIT 1
            """
            progress_result = items_db.execute_query(progress_query, (task_id,))

            if progress_result:
                status = progress_result[0].get("status")
                if status == "processing":
                    result["extraction_in_progress"] = True
                elif status == "completed":
                    result["extraction_completed"] = True

            items_db.disconnect()

            self.logger.info(
                "HomeContentModel: スナップショットと抽出計画の確認完了",
                task_id=task_id,
                result=result,
            )
            return result

        except Exception as e:
            self.logger.error(
                "HomeContentModel: スナップショットと抽出計画の確認エラー",
                task_id=task_id,
                error=str(e),
            )
            return result

    def create_outlook_snapshot(self, task_id: str) -> bool:
        """
        outlook.dbのfoldersテーブルの状態をitems.dbのoutlook_snapshotテーブルに記録する

        Args:
            task_id: タスクID

        Returns:
            bool: 記録が成功したかどうか
        """
        try:
            # OutlookExtractionServiceを使用してスナップショットを作成
            extraction_service = OutlookExtractionService(task_id)

            # 初期化に失敗した場合
            if not extraction_service.initialize():
                self.logger.error(
                    "HomeContentModel: OutlookExtractionServiceの初期化に失敗しました",
                    task_id=task_id,
                )
                return False

            try:
                # スナップショット作成を実行
                success = extraction_service.create_snapshot()
                return success
            except Exception as e:
                self.logger.error(
                    "HomeContentModel: スナップショット作成中にエラーが発生しました",
                    task_id=task_id,
                    error=str(e),
                )
                return False
            finally:
                # 必ずリソースを解放
                extraction_service.cleanup()

        except Exception as e:
            self.logger.error(
                "HomeContentModel: Outlookスナップショット作成エラー",
                task_id=task_id,
                error=str(e),
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
            # まずスナップショットと抽出計画の状態を確認
            status = self.check_snapshot_and_extraction_plan(task_id)

            # OutlookExtractionServiceを使用して抽出を開始
            extraction_service = OutlookExtractionService(task_id)

            # 初期化に失敗した場合
            if not extraction_service.initialize():
                self.logger.error(
                    "HomeContentModel: OutlookExtractionServiceの初期化に失敗しました",
                    task_id=task_id,
                )
                return False

            try:
                # 既に抽出が完了している場合は成功として返す
                if status["extraction_completed"]:
                    self.logger.info(
                        "HomeContentModel: メール抽出は既に完了しています",
                        task_id=task_id,
                    )
                    return True

                # 抽出が進行中の場合も成功として返す
                if status["extraction_in_progress"]:
                    self.logger.info(
                        "HomeContentModel: メール抽出は既に進行中です", task_id=task_id
                    )
                    return True

                # 抽出作業を開始
                success = extraction_service.start_extraction()
                return success
            except Exception as e:
                self.logger.error(
                    "HomeContentModel: メール抽出作業中にエラーが発生しました",
                    task_id=task_id,
                    error=str(e),
                )
                return False
            finally:
                # 必ずリソースを解放
                extraction_service.cleanup()

        except Exception as e:
            self.logger.error(
                "HomeContentModel: メール抽出作業エラー", task_id=task_id, error=str(e)
            )
            return False

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

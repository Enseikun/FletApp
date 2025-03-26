import os
from typing import List, Optional, Tuple

from src.core.database import DatabaseManager
from src.core.logger import get_logger


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
                from src.core.database import DatabaseManager

                db_manager = DatabaseManager(items_db_path)
                self.logger.info(
                    f"HomeContentModel: items.dbを作成しました - {items_db_path}"
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
            task_data = [(item["id"], item["from_folder_name"]) for item in results]
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
            self.logger.info("HomeContentModel: タスク削除開始", task_id=task_id)

            # トランザクション開始
            self.db_manager.begin_transaction()

            # タスク情報を削除
            query = "DELETE FROM task_info WHERE id = ?"
            self.db_manager.execute_update(query, (task_id,))

            # トランザクションコミット
            self.db_manager.commit_transaction()

            # タスクディレクトリとその中身を削除
            task_dir = os.path.join("data", "tasks", str(task_id))
            if os.path.exists(task_dir):
                import shutil

                shutil.rmtree(task_dir)
                self.logger.info(
                    f"HomeContentModel: タスクディレクトリを削除しました - {task_dir}"
                )

            self.logger.info("HomeContentModel: タスク削除成功", task_id=task_id)
            return True
        except Exception as e:
            # エラー時はロールバック
            self.db_manager.rollback_transaction()
            self.logger.error(
                "HomeContentModel: タスク削除エラー", task_id=task_id, error=str(e)
            )
            return False

    def create_outlook_snapshot(self, task_id: str) -> bool:
        """
        outlook.dbのfoldersテーブルの状態をitems.dbのoutlook_snapshotテーブルに記録する

        Args:
            task_id: タスクID

        Returns:
            bool: 記録が成功したかどうか
        """
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

            # outlook.dbからfoldersテーブルのデータを取得
            folders_data = outlook_db.execute_query("SELECT * FROM folders")

            # outlook_snapshotテーブルにデータを挿入
            for folder in folders_data:
                query = """
                INSERT INTO outlook_snapshot (
                    folder_id, folder_name, parent_folder_id, folder_path,
                    folder_type, folder_class, total_items, unread_items,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """
                params = (
                    folder["id"],
                    folder["name"],
                    folder["parent_folder_id"],
                    folder["folder_path"],
                    folder["folder_type"],
                    folder["folder_class"],
                    folder["total_items"],
                    folder["unread_items"],
                )
                items_db.execute_update(query, params)

            self.logger.info(
                "HomeContentModel: Outlookスナップショット作成成功", task_id=task_id
            )
            return True

        except Exception as e:
            self.logger.error(
                "HomeContentModel: Outlookスナップショット作成エラー",
                task_id=task_id,
                error=str(e),
            )
            return False

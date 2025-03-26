"""
タスク内容モデル
タスク情報の保存と取得を担当
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.database import DatabaseManager
from src.core.logger import get_logger


class TaskContentModel:
    """タスク内容モデル"""

    def __init__(self):
        """初期化"""
        self.logger = get_logger()
        self._tasks_db = DatabaseManager("data/tasks.db")
        self._outlook_db = DatabaseManager("data/outlook.db")

    def create_task(self, task_info: Dict[str, Any]) -> bool:
        """タスクを作成"""
        try:
            # OutlookDBからフォルダ情報を取得
            folder_info = self._get_folder_info(task_info["from_folder_id"])
            if not folder_info:
                self.logger.error("フォルダ情報の取得に失敗しました")
                return False

            # ViewModelで未設定のタスク情報を更新
            task_info.update(
                {
                    "account_id": folder_info["account_id"],
                    "folder_id": folder_info["folder_id"],
                    "from_folder_id": folder_info["folder_id"],
                    "from_folder_name": folder_info["folder_name"],
                    "from_folder_path": folder_info["folder_path"],
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

            # 移動先フォルダの情報も取得
            if task_info["to_folder_id"]:
                to_folder_info = self._get_folder_info(task_info["to_folder_id"])
                if to_folder_info:
                    task_info.update(
                        {
                            "to_folder_id": to_folder_info["folder_id"],
                            "to_folder_name": to_folder_info["folder_name"],
                            "to_folder_path": to_folder_info["folder_path"],
                        }
                    )

            # タスク情報を保存
            self._save_task_info(task_info)
            return True

        except Exception as e:
            self.logger.error(f"タスクの作成に失敗しました: {str(e)}")
            return False

    def _get_folder_info(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """OutlookDBからフォルダ情報を取得"""
        try:
            query = """
            SELECT 
                f.entry_id as folder_id,
                f.name as folder_name,
                f.path as folder_path,
                a.store_id as account_id
            FROM folders f
            JOIN accounts a ON f.store_id = a.store_id
            WHERE f.entry_id = ?
            """
            result = self._outlook_db.execute_query(query, (entry_id,))

            if result:
                return result[0]
            return None

        except Exception as e:
            self.logger.error(f"フォルダ情報の取得に失敗しました: {str(e)}")
            return None

    def _save_task_info(self, task_info: Dict[str, Any]):
        """タスク情報を保存"""
        try:
            query = """
            INSERT INTO task_info (
                id, account_id, folder_id, from_folder_id, from_folder_name,
                from_folder_path, to_folder_id, to_folder_name, to_folder_path,
                start_date, end_date, ai_review, file_download,
                exclude_extensions, status, created_at, updated_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """
            params = (
                task_info["id"],
                task_info["account_id"],
                task_info["folder_id"],
                task_info["from_folder_id"],
                task_info["from_folder_name"],
                task_info["from_folder_path"],
                task_info.get("to_folder_id"),
                task_info.get("to_folder_name"),
                task_info.get("to_folder_path"),
                task_info["start_date"],
                task_info["end_date"],
                task_info["ai_review"],
                task_info["file_download"],
                ",".join(task_info["exclude_extensions"]),
                task_info["status"],
                task_info["created_at"],
                task_info["updated_at"],
            )
            self._tasks_db.execute_update(query, params)

        except Exception as e:
            self.logger.error(f"タスク情報の保存に失敗しました: {str(e)}")
            raise

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
                    f"TaskContentModel: タスクフォルダを作成しました - {task_dir}"
                )

            # items.dbのパスを設定
            items_db_path = os.path.join(task_dir, "items.db")

            # items.dbが存在しない場合のみ作成
            if not os.path.exists(items_db_path):
                from src.core.database import DatabaseManager

                db_manager = DatabaseManager(items_db_path)
                self.logger.info(
                    f"TaskContentModel: items.dbを作成しました - {items_db_path}"
                )

            return True
        except Exception as e:
            self.logger.error(
                f"TaskContentModel: タスクフォルダまたはデータベースの作成に失敗しました - {e}"
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
                "TaskContentModel: Outlookスナップショット作成開始", task_id=task_id
            )

            # items.dbのパスを設定
            items_db_path = os.path.join("data", "tasks", str(task_id), "items.db")
            items_db = DatabaseManager(items_db_path)

            # outlook.dbからfoldersテーブルのデータを取得
            folders_data = self._outlook_db.execute_query("SELECT * FROM folders")

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
                    folder["entry_id"],
                    folder["name"],
                    folder["parent_folder_id"],
                    folder["path"],
                    folder["folder_type"],
                    folder["folder_class"],
                    folder["item_count"],
                    folder["unread_count"],
                )
                items_db.execute_update(query, params)

            self.logger.info(
                "TaskContentModel: Outlookスナップショット作成成功", task_id=task_id
            )
            return True

        except Exception as e:
            self.logger.error(
                "TaskContentModel: Outlookスナップショット作成エラー",
                task_id=task_id,
                error=str(e),
            )
            return False

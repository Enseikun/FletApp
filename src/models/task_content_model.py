"""
タスク内容モデル
タスク情報の保存と取得を担当
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.database import DatabaseManager
from src.core.logger import get_logger
from src.util.object_util import get_safe


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
            folder_info = self._get_folder_info(get_safe(task_info, "from_folder_id"))
            if not folder_info:
                self.logger.error("フォルダ情報の取得に失敗しました")
                return False

            # ViewModelで未設定のタスク情報を更新
            task_info.update(
                {
                    "account_id": get_safe(folder_info, "store_id"),
                    "folder_id": get_safe(folder_info, "entry_id"),
                    "from_folder_id": get_safe(folder_info, "entry_id"),
                    "from_folder_name": get_safe(folder_info, "name"),
                    "from_folder_path": get_safe(folder_info, "path"),
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

            # 移動先フォルダの情報も取得
            if get_safe(task_info, "to_folder_id"):
                to_folder_info = self._get_folder_info(
                    get_safe(task_info, "to_folder_id")
                )
                if to_folder_info:
                    task_info.update(
                        {
                            "to_folder_id": get_safe(to_folder_info, "entry_id"),
                            "to_folder_name": get_safe(to_folder_info, "name"),
                            "to_folder_path": get_safe(to_folder_info, "path"),
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
                f.entry_id,
                f.name,
                f.path,
                f.store_id
            FROM folders f
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
                get_safe(task_info, "id"),
                get_safe(task_info, "account_id"),
                get_safe(task_info, "folder_id"),
                get_safe(task_info, "from_folder_id"),
                get_safe(task_info, "from_folder_name"),
                get_safe(task_info, "from_folder_path"),
                get_safe(task_info, "to_folder_id"),
                get_safe(task_info, "to_folder_name"),
                get_safe(task_info, "to_folder_path"),
                get_safe(task_info, "start_date"),
                get_safe(task_info, "end_date"),
                get_safe(task_info, "ai_review"),
                get_safe(task_info, "file_download"),
                ",".join(get_safe(task_info, "exclude_extensions", [])),
                get_safe(task_info, "status"),
                get_safe(task_info, "created_at"),
                get_safe(task_info, "updated_at"),
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

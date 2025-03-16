import os
from typing import Any, Dict, List, Tuple

from src.core.database import DatabaseManager


class HomeContentViewModel:
    """
    ホーム画面のコンテンツ用ViewModel
    tasks.dbからデータを取得して提供する
    """

    def __init__(self, db_path: str = None):
        """初期化"""
        # デフォルトのデータベースパスを設定
        if db_path is None:
            # プロジェクトのルートディレクトリを基準にデータベースパスを設定
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data",
                "tasks.db",
            )
            print(f"データベースパス: {db_path}")

        self.db_manager = DatabaseManager(db_path)

    def get_tasks_data(self) -> List[Tuple[int, str]]:
        """
        tasks.dbからタスクデータを取得する

        Returns:
            List[Tuple[int, str]]: (id, from_folder_name)のリスト
        """
        try:
            # DatabaseManagerを使用してクエリを実行
            query = "SELECT id, from_folder_name FROM task_info"
            results = self.db_manager.execute_query(query)

            # 辞書のリストをタプルのリストに変換
            return [(item["id"], item["from_folder_name"]) for item in results]
        except Exception as e:
            print(f"タスクデータ取得エラー: {e}")
            return []

import os
from typing import Any, Dict, List, Tuple

from src.core.logger import get_logger
from src.models.home_content_model import HomeContentModel


class HomeContentViewModel:
    """
    ホーム画面のコンテンツ用ViewModel
    tasks.dbからデータを取得して提供する
    """

    def __init__(self, db_path: str = None):
        """初期化"""
        self.logger = get_logger()
        self.logger.info("HomeContentViewModel: 初期化開始", db_path=db_path)
        self.model = HomeContentModel(db_path)
        self.current_task_id = None
        self.main_viewmodel = None  # MainViewModelへの参照を保持するためのプロパティ
        self.logger.info("HomeContentViewModel: 初期化完了")

    def get_tasks_data(self) -> List[Tuple[int, str]]:
        """
        tasks.dbからタスクデータを取得する

        Returns:
            List[Tuple[int, str]]: (id, from_folder_name)のリスト
        """
        self.logger.debug("HomeContentViewModel: タスクデータ取得開始")
        result = self.model.get_tasks_data()
        self.logger.debug(
            "HomeContentViewModel: タスクデータ取得完了", task_count=len(result)
        )
        return result

    def delete_task(self, task_id: str) -> bool:
        """
        指定されたIDのタスクを削除する

        Args:
            task_id: 削除するタスクのID

        Returns:
            bool: 削除が成功したかどうか
        """
        self.logger.info("HomeContentViewModel: タスク削除開始", task_id=task_id)
        result = self.model.delete_task(task_id)
        if result:
            self.logger.info("HomeContentViewModel: タスク削除成功", task_id=task_id)
        else:
            self.logger.error("HomeContentViewModel: タスク削除失敗", task_id=task_id)
        return result

    def set_current_task_id(self, task_id: str) -> None:
        """
        現在選択されているタスクIDを設定する

        Args:
            task_id: 設定するタスクID
        """
        self.current_task_id = task_id
        self.logger.info("HomeContentViewModel: 現在のタスクIDを設定", task_id=task_id)

        # MainViewModelが設定されている場合、そちらにも通知する
        if self.main_viewmodel:
            self.main_viewmodel.set_current_task_id(task_id)
            self.logger.debug(
                "HomeContentViewModel: MainViewModelにタスクIDを設定", task_id=task_id
            )

    def get_current_task_id(self) -> str:
        """
        現在選択されているタスクIDを取得する

        Returns:
            str: 現在のタスクID
        """
        self.logger.debug(
            "HomeContentViewModel: 現在のタスクIDを取得", task_id=self.current_task_id
        )
        return self.current_task_id

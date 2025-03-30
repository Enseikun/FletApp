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

    def set_current_task_id(self, task_id: str) -> bool:
        """
        現在選択されているタスクIDを設定する

        Args:
            task_id: 設定するタスクID

        Returns:
            bool: 処理が成功したかどうか
        """
        self.current_task_id = task_id
        self.logger.info("HomeContentViewModel: 現在のタスクIDを設定", task_id=task_id)

        success = True

        # スナップショットを作成
        if task_id:
            # スナップショットと抽出計画の状態を確認
            status = self.check_snapshot_and_extraction_plan(task_id)

            # スナップショットが存在しない場合は作成
            if not status["has_snapshot"]:
                self.logger.info(
                    f"HomeContentViewModel: スナップショットが存在しないため作成します - {task_id}"
                )
                snapshot_success = self.create_outlook_snapshot(task_id)
                if not snapshot_success:
                    self.logger.error(
                        "HomeContentViewModel: スナップショットの作成に失敗しました",
                        task_id=task_id,
                    )
                    success = False
                    return success  # スナップショットの作成に失敗した場合は処理を中止

            # スナップショットが存在し、抽出計画が存在しないか、または抽出が完了していない場合はメール抽出を開始
            if status["has_snapshot"] and (
                not status["has_extraction_plan"]
                or (
                    not status["extraction_in_progress"]
                    and not status["extraction_completed"]
                )
            ):
                self.logger.info(
                    f"HomeContentViewModel: メール抽出を開始します - {task_id}"
                )
                extraction_success = self.start_mail_extraction(task_id)
                if not extraction_success:
                    self.logger.error(
                        "HomeContentViewModel: メール抽出の開始に失敗しました",
                        task_id=task_id,
                    )
                    success = False
                else:
                    self.logger.info(
                        "HomeContentViewModel: メール抽出を開始しました",
                        task_id=task_id,
                    )
            elif status["extraction_in_progress"]:
                self.logger.info(
                    f"HomeContentViewModel: メール抽出は既に進行中です - {task_id}"
                )
            elif status["extraction_completed"]:
                self.logger.info(
                    f"HomeContentViewModel: メール抽出は既に完了しています - {task_id}"
                )

        # MainViewModelが設定されている場合、そちらにも通知する
        if self.main_viewmodel and success:
            self.main_viewmodel.set_current_task_id(task_id)
            self.logger.debug(
                "HomeContentViewModel: MainViewModelにタスクIDを設定", task_id=task_id
            )

        return success

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

    def create_task_directory_and_database(self, task_id: str) -> bool:
        """
        タスクフォルダとデータベースを作成する

        Args:
            task_id: タスクID

        Returns:
            bool: 作成が成功したかどうか
        """
        self.logger.info(
            "HomeContentViewModel: タスクフォルダとデータベースの作成開始",
            task_id=task_id,
        )
        result = self.model.create_task_directory_and_database(task_id)
        if result:
            self.logger.info(
                "HomeContentViewModel: タスクフォルダとデータベースの作成成功",
                task_id=task_id,
            )
        else:
            self.logger.error(
                "HomeContentViewModel: タスクフォルダとデータベースの作成失敗",
                task_id=task_id,
            )
        return result

    def check_snapshot_and_extraction_plan(self, task_id: str) -> Dict[str, bool]:
        """
        スナップショットと抽出計画の存在を確認する

        Args:
            task_id: タスクID

        Returns:
            Dict[str, bool]: スナップショットと抽出計画の存在状況
        """
        self.logger.info(
            "HomeContentViewModel: スナップショットと抽出計画の確認開始",
            task_id=task_id,
        )
        result = self.model.check_snapshot_and_extraction_plan(task_id)
        self.logger.info(
            "HomeContentViewModel: スナップショットと抽出計画の確認完了",
            task_id=task_id,
            result=result,
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
        self.logger.info(
            "HomeContentViewModel: Outlookスナップショット作成開始", task_id=task_id
        )
        result = self.model.create_outlook_snapshot(task_id)
        if result:
            self.logger.info(
                "HomeContentViewModel: Outlookスナップショット作成成功", task_id=task_id
            )
        else:
            self.logger.error(
                "HomeContentViewModel: Outlookスナップショット作成失敗", task_id=task_id
            )
        return result

    def start_mail_extraction(self, task_id: str) -> bool:
        """
        メール抽出作業を開始する

        Args:
            task_id: タスクID

        Returns:
            bool: 開始が成功したかどうか
        """
        self.logger.info("HomeContentViewModel: メール抽出開始", task_id=task_id)
        result = self.model.start_mail_extraction(task_id)
        if result:
            self.logger.info(
                "HomeContentViewModel: メール抽出開始成功", task_id=task_id
            )
        else:
            self.logger.error(
                "HomeContentViewModel: メール抽出開始失敗", task_id=task_id
            )
        return result

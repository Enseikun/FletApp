from src.core.logger import get_logger
from src.viewmodels.home_content_viewmodel import HomeContentViewModel


class HomeViewModel:
    """ホーム画面のViewModel"""

    def __init__(self, main_viewmodel):
        """初期化"""
        self.main_viewmodel = main_viewmodel
        self.selected_task_id = None
        self.tasks = []  # タスクのリスト
        self.content_viewmodel = HomeContentViewModel()
        self.logger = get_logger()  # ロガーを初期化

    def load_tasks(self):
        """利用可能なタスクを読み込む"""
        # データベースからタスクリストを取得
        task_data = self.content_viewmodel.get_tasks_data()

        # タスクデータを整形
        self.tasks = [
            {"id": task_id, "from_folder_name": folder_name}
            for task_id, folder_name in task_data
        ]

        return self.tasks

    async def select_task(self, task_id):
        """タスクを選択する"""
        self.selected_task_id = task_id

        # ログを追加して確認
        self.logger.debug(
            f"HomeViewModel.select_task: タスク選択処理開始", task_id=task_id
        )

        # メインViewModelに選択されたタスクIDを設定
        if self.main_viewmodel:
            # content_viewmodelにタスクIDを設定し、成功したかどうかを確認
            success = await self.content_viewmodel.set_current_task_id(task_id)

            if not success:
                # エラーがあった場合は画面遷移をしない
                self.logger.error(
                    f"HomeViewModel.select_task: タスク選択処理に失敗しました",
                    task_id=task_id,
                )
                return False

            # main_viewmodelがMainContentsViewModelの場合、そのmain_viewmodelプロパティを使用
            if (
                hasattr(self.main_viewmodel, "main_viewmodel")
                and self.main_viewmodel.main_viewmodel
            ):
                self.main_viewmodel.main_viewmodel.set_current_task_id(task_id)
                # プレビュー画面に遷移
                self.main_viewmodel.main_viewmodel.set_destination("preview")
                self.logger.info(
                    f"HomeViewModel.select_task: プレビュー画面に遷移しました(MainContentsViewModel経由)",
                    task_id=task_id,
                )
                return True

            # 通常のMainViewModelの場合
            self.main_viewmodel.set_current_task_id(task_id)
            self.main_viewmodel.set_destination("preview")
            self.logger.info(
                f"HomeViewModel.select_task: プレビュー画面に遷移しました(直接MainViewModel経由)",
                task_id=task_id,
            )
            return True

        self.logger.warning(
            f"HomeViewModel.select_task: MainViewModelが設定されていません",
            task_id=task_id,
        )
        return False

    def delete_task(self, task_id):
        """タスクを削除する"""
        success = self.content_viewmodel.delete_task(task_id)
        if success:
            # タスクリストを再読み込み
            self.load_tasks()
        return success

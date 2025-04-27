"""
メインコンテンツコンポーネント
アプリケーションのメインコンテンツ領域を管理
"""

import flet as ft

from src.core.logger import get_logger
from src.viewmodels.home_content_viewmodel import HomeContentViewModel
from src.viewmodels.main_contents_viewmodel import MainContentsViewModel
from src.views.contents.content_factory import create_content


class MainContents(ft.Container):
    """
    アプリケーションのメインコンテンツ
    サイドバーの選択に応じて表示内容を切り替える
    """

    def __init__(self, main_viewmodel=None):
        """
        初期化

        Args:
            main_viewmodel (MainViewModel, optional): メインビューモデル
        """
        super().__init__()
        self.logger = get_logger()
        self.logger.info("MainContents初期化開始")
        self._main_viewmodel = main_viewmodel
        self._contents_viewmodel = MainContentsViewModel(main_viewmodel)
        self.expand = True

        # ローディングインジケーター
        self._loading_indicator = ft.Column(
            controls=[
                ft.Container(
                    content=ft.ProgressRing(),
                    alignment=ft.alignment.center,
                    expand=True,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )

        # 実際のコンテンツ
        self._actual_content = None

        # ViewModelの監視を登録
        self._contents_viewmodel.add_observer(self)

        # ビューモデルの変更を監視
        if self._main_viewmodel:
            self._main_viewmodel.add_destination_changed_callback(self.update_content)
            # 初期状態を設定
            initial_destination = self._main_viewmodel.get_current_destination()
            self._main_viewmodel.set_initial_destination(initial_destination)
            # 初期コンテンツを設定
            self._home_content_viewmodel = HomeContentViewModel()
            if initial_destination == "home":
                self._actual_content = create_content(
                    initial_destination, self._home_content_viewmodel
                )
            else:
                self._actual_content = create_content(
                    initial_destination, self._contents_viewmodel
                )
            self.content = self._actual_content
            self.logger.info("MainContents初期化完了")

    def update_content(self, destination_key):
        """
        表示するコンテンツを更新

        Args:
            destination_key (str): 表示するコンテンツのキー
        """
        self.logger.info(f"MainContents: 表示コンテンツを更新 - {destination_key}")

        # ローディング状態を表示
        self._contents_viewmodel.set_loading(True)
        self.content = self._loading_indicator
        self.update()

        # HomeContentの場合はHomeContentViewModelを渡す
        if destination_key == "home":
            new_content = create_content(destination_key, self._home_content_viewmodel)
        else:
            new_content = create_content(destination_key, self._contents_viewmodel)
        self._actual_content = new_content

        # ローディング状態を解除
        self._contents_viewmodel.set_loading(False)

    def on_view_model_changed(self):
        """ViewModelの変更通知を受け取るコールバック"""
        self.logger.debug("MainContents: ViewModelの変更を検知")

        # ローディング状態に応じてコンテンツを切り替え
        if self._contents_viewmodel.is_loading():
            self.content = self._loading_indicator
        else:
            self.content = self._actual_content

        self.update()

    def create_content_for_destination(self, destination_key):
        """
        指定されたDestination用のコンテンツを作成する

        Args:
            destination_key: Destinationのキー

        Returns:
            作成されたコンテンツ
        """
        self.logger.debug(f"コンテンツ作成: {destination_key}")
        # HomeContentの場合はHomeContentViewModelを渡す
        if destination_key == "home":
            return create_content(destination_key, self._home_content_viewmodel)
        else:
            return create_content(destination_key, self._contents_viewmodel)

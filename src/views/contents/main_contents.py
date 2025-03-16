"""
メインコンテンツコンポーネント
アプリケーションのメインコンテンツ領域を管理
"""

import flet as ft

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
        self._main_viewmodel = main_viewmodel
        self._contents_viewmodel = MainContentsViewModel(main_viewmodel)
        self.expand = True

        # ViewModelの監視を登録
        self._contents_viewmodel.add_observer(self)

        # ビューモデルの変更を監視
        if self._main_viewmodel:
            self._main_viewmodel.add_destination_changed_callback(self.update_content)
            # 初期状態を設定（updateは呼ばない）
            self._main_viewmodel.set_initial_destination("home")

    def update_content(self, destination_key):
        """
        表示するコンテンツを更新

        Args:
            destination_key (str): 表示するコンテンツのキー
        """
        print(f"MainContents: 表示コンテンツを更新 - {destination_key}")

        # コンテンツファクトリからコンテンツを取得
        new_content = create_content(destination_key, self._contents_viewmodel)

        # コンテンツを更新
        self.content = new_content
        self.update()

    def on_view_model_changed(self):
        """ViewModelの変更通知を受け取るコールバック"""
        self.update()

    def create_content_for_destination(self, destination_key):
        """
        指定されたDestination用のコンテンツを作成する

        Args:
            destination_key: Destinationのキー

        Returns:
            作成されたコンテンツ
        """
        # コンテンツファクトリからコンテンツを取得
        return create_content(destination_key)

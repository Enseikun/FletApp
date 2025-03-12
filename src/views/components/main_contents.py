"""
メインコンテンツコンポーネント
アプリケーションのメインコンテンツ領域を管理
"""

import flet as ft

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
        self.main_viewmodel = main_viewmodel
        self.current_content = None

        # 親クラスの初期化
        super().__init__(
            content=ft.Text("コンテンツを読み込み中..."), expand=True, padding=10
        )

        # ビューモデルが提供されている場合、コールバックを登録
        if self.main_viewmodel:
            self.main_viewmodel.add_destination_changed_callback(self.update_content)

    def update_content(self, destination_key):
        """
        表示するコンテンツを更新

        Args:
            destination_key (str): 表示するコンテンツのキー
        """
        # コンテンツファクトリからコンテンツを取得
        new_content = create_content(destination_key)

        # コンテンツを更新
        self.content = new_content
        self.current_content = new_content
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

    def _get_control_name(self):
        return "main_contents"

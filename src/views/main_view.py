"""
アプリケーションのメインビュー
Fletを使用したAppBar、SideBar、MainContentsを表示するシングルページアプリケーション
"""

import flet as ft

from src.views.components.app_bar import AppBar
from src.views.components.main_contents import MainContents
from src.views.components.side_bar import SideBar


class MainView(ft.View):
    """
    アプリケーションのメインビュー
    AppBar、SideBar、MainContentsを含むシングルページアプリケーション
    """

    def __init__(self):
        super().__init__()

        # UI
        self.page.appbar = AppBar(title=ft.Text("TestApp"))
        self.side_bar = SideBar()
        self.main_contents = MainContents()

        # レイアウトの構成
        self.content = ft.Row(
            [
                self.side_bar,
                ft.VerticalDivider(width=1),
                self.main_contents,
            ],
            expand=True,
        )

        # サイドバーのイベントハンドラを設定
        self.side_bar.on_destination_change = self.handle_destination_change

        # 初期表示を設定
        self.handle_destination_change("home")

    def handle_destination_change(self, destination_key):
        """
        サイドバーのDestination変更を処理する

        Args:
            destination_key: 選択されたDestinationのキー
        """
        # メインコンテンツを更新
        self.main_contents.update_content(destination_key)
        self.update()


def create_main_view():
    """MainViewのインスタンスを作成して返す"""
    return MainView()

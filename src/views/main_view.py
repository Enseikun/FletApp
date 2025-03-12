"""
アプリケーションのメインビュー
Fletを使用したAppBar、SideBar、MainContentsを表示するシングルページアプリケーション
"""

import flet as ft

from src.viewmodels.main_viewmodel import MainViewModel
from src.viewmodels.sidebar_viewmodel import SideBarViewModel
from src.views.components.main_contents import MainContents
from src.views.components.side_bar import SideBar


class MainView(ft.Container):
    """
    アプリケーションのメインビュー
    AppBar、SideBar、MainContentsを含むシングルページアプリケーション
    """

    def __init__(self, page=None):
        self.page = page

        # UI
        if self.page is not None:
            self.page.appbar = ft.AppBar(title=ft.Text("TestApp"))

        # ビューモデルの初期化
        self.main_viewmodel = MainViewModel()
        self.sidebar_viewmodel = SideBarViewModel(self.main_viewmodel)

        # コンポーネントの初期化（ビューモデルを渡す）
        self.side_bar = SideBar(viewmodel=self.sidebar_viewmodel)
        self.main_contents = MainContents(main_viewmodel=self.main_viewmodel)

        # レイアウトの構成
        content = ft.Row(
            [
                self.side_bar,
                ft.VerticalDivider(width=1),
                self.main_contents,
            ],
            expand=True,
        )

        # 親クラスの初期化
        super().__init__(content=content, expand=True)

        # 初期表示を設定（ページがレンダリングされた後に実行）
        if self.page:
            self.page.on_load = lambda _: self.main_viewmodel.set_destination("home")
        else:
            # ページがない場合は直接設定
            self.main_viewmodel.set_destination("home")


def create_main_view(page=None):
    """MainViewのインスタンスを作成して返す"""
    return MainView(page)

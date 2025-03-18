"""
アプリケーションのメインビュー
Fletを使用したAppBar、SideBar、MainContentsを表示するシングルページアプリケーション
"""

import flet as ft

from src.core.logger import get_logger
from src.viewmodels.main_viewmodel import MainViewModel
from src.viewmodels.sidebar_viewmodel import SideBarViewModel
from src.views.components.side_bar import SideBar
from src.views.contents.main_contents import MainContents


class MainView(ft.Container):
    """
    アプリケーションのメインビュー
    AppBar、SideBar、MainContentsを含むシングルページアプリケーション
    """

    def __init__(self, page=None):
        super().__init__()
        self.page = page
        self.logger = get_logger()
        self.logger.info("MainView初期化開始")

        # UI
        if self.page is not None:
            self.page.appbar = ft.AppBar(title=ft.Text("TestApp"))

        # ビューモデルの初期化
        self.main_viewmodel = MainViewModel()
        self.sidebar_viewmodel = SideBarViewModel(self.main_viewmodel)

        # ここで明示的にサイドバーViewModelを設定
        self.main_viewmodel.set_sidebar_viewmodel(self.sidebar_viewmodel)

        # コンポーネントの初期化（ビューモデルを渡す）
        self.side_bar = SideBar(viewmodel=self.sidebar_viewmodel)
        self.main_contents = MainContents(main_viewmodel=self.main_viewmodel)

        # レイアウトの構成
        content = ft.Row(
            [
                self.side_bar,
                ft.VerticalDivider(width=1),
                # MainContentsをColumnでラップ
                ft.Column(
                    [self.main_contents],
                    expand=True,  # Columnが水平方向に拡大
                ),
            ],
            expand=True,
        )

        # 親クラスの初期化
        super().__init__(content=content, expand=True)
        self.logger.info("MainViewレイアウト構成完了")

        # ページがある場合、ページの準備完了後に初期デスティネーションを設定
        if self.page:

            def _on_view_ready(_):
                # コンポーネントがページに追加された後で初期デスティネーションを設定
                self.main_viewmodel.set_destination("home")
                self.expand = True
                self.logger.info("初期デスティネーション設定: home")
                # 一度限りのイベントなのでリスナーを削除
                self.page.on_view_ready.remove(_on_view_ready)

            self.page.on_view_ready.append(_on_view_ready)


def create_main_view(page=None):
    """MainViewのインスタンスを作成して返す"""
    logger = get_logger()
    logger.info("MainViewインスタンス作成")
    return MainView(page)

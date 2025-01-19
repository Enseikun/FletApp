import flet as ft

from presenters.interfaces.presenter_interface import PresenterInterface
from router import Router


class MainPresenter(PresenterInterface):
    def __init__(self, page: ft.Page):
        self.page = page
        self.router = Router(page)

    def initialize(self):
        """アプリケーション起動時の初期化処理"""
        self.show_first_view()

    def show_first_view(self, data: dict = None):
        try:
            view = self.router.navigate("/", data)
            view.display()
        except ValueError as e:
            print(f"Navigation error: {e}")

    def show_second_view(self, data: dict = None):
        try:
            view = self.router.navigate("/second", data)
            view.display()
        except ValueError as e:
            print(f"Navigation error: {e}")

    def handle_user_input(self, data: any) -> None:
        """ユーザー入力の処理（必要に応じて実装）"""
        pass

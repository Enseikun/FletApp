import flet as ft

from src.views.components.app_bar import AppBar


class MenuView(ft.View):
    def __init__(self, route: str = None, **kwargs) -> None:
        super().__init__()
        self.route = route
        self.appbar = AppBar("メニュー").build()
        self.controls = []

    def build(self):
        return self

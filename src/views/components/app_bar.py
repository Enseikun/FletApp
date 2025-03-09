import flet as ft

from src.views.styles.color import Colors


class AppBar(ft.AppBar):
    def __init__(self, title: ft.Control) -> None:
        super().__init__()
        self.title = title

    def build(self):
        return ft.AppBar(
            title=self.title,
            bgcolor=Colors.PRIMARY,
        )

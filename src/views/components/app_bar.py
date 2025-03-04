import flet as ft

from src.views.style.colors import ON_PRIMARY, PRIMARY


class AppBar:
    def __init__(self, title: str) -> None:
        self.title = title

    def build(self):
        return ft.AppBar(
            title=ft.Text(
                self.title,
                color=ON_PRIMARY,
            ),
            bgcolor=PRIMARY,
        )

import flet as ft


class SettingsContent(ft.Column):
    """設定画面のコンテンツ"""

    def __init__(self):
        super().__init__(
            controls=[
                ft.Text("設定画面", size=24, weight=ft.FontWeight.BOLD),
                ft.Switch(label="ダークモード"),
                ft.Dropdown(
                    label="言語",
                    options=[
                        ft.dropdown.Option("日本語"),
                        ft.dropdown.Option("English"),
                    ],
                    width=200,
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=20,
        )

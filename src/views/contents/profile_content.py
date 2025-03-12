import flet as ft


class ProfileContent(ft.Column):
    """プロフィール画面のコンテンツ"""

    def __init__(self):
        super().__init__(
            controls=[
                ft.Text("プロフィール画面", size=24, weight=ft.FontWeight.BOLD),
                ft.TextField(label="ユーザー名", width=300),
                ft.TextField(label="メールアドレス", width=300),
                ft.ElevatedButton("保存"),
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=20,
        )

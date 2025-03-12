import flet as ft


class HomeContent(ft.Container):
    """
    ホーム画面のダミーコンテンツを表示するウィジェット
    """

    def __init__(self):
        # ダミーコンテンツを作成
        content = ft.Column(
            [
                ft.Text("ホームコンテンツ", size=30, weight=ft.FontWeight.BOLD),
                ft.Text("これはダミーのホームコンテンツです。", size=16),
                ft.Divider(),
                ft.Container(
                    content=ft.Text("サンプルカード", size=20),
                    padding=20,
                    margin=10,
                    bgcolor=ft.colors.BLUE_50,
                    border_radius=10,
                    width=300,
                ),
                ft.Container(
                    content=ft.Text("もう一つのサンプルカード", size=20),
                    padding=20,
                    margin=10,
                    bgcolor=ft.colors.GREEN_50,
                    border_radius=10,
                    width=300,
                ),
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

        # 親クラスの初期化
        super().__init__(
            content=content,
            padding=20,
            expand=True,
        )

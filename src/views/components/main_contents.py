import flet as ft


class MainContents(ft.Container):
    def __init__(self):
        super().__init__(
            expand=True,
            padding=20,
        )

        # 各Destinationのコンテンツをキャッシュする辞書
        self.content_cache = {}

        # 現在選択されているDestination
        self.current_destination = None

        # デフォルトのコンテンツ
        self.content = ft.Text("メインコンテンツがここに表示されます", size=20)

    def update_content(self, destination_key):
        """
        メインコンテンツエリアを更新する

        Args:
            destination_key: 表示するコンテンツのキー
        """
        # 既に同じDestinationが選択されている場合は何もしない
        if self.current_destination == destination_key:
            return

        # 現在のDestinationを更新
        self.current_destination = destination_key

        # キャッシュにコンテンツがあればそれを使用、なければ新しく作成
        if destination_key not in self.content_cache:
            self.content_cache[destination_key] = self.create_content_for_destination(
                destination_key
            )

        # コンテンツを更新
        self.content = self.content_cache[destination_key]

    def create_content_for_destination(self, destination_key):
        """
        指定されたDestination用のコンテンツを作成する

        Args:
            destination_key: Destinationのキー

        Returns:
            作成されたコンテンツ
        """
        # 各Destinationに応じたコンテンツを作成
        if destination_key == "home":
            return ft.Column(
                [
                    ft.Text("ホーム画面", size=24, weight=ft.FontWeight.BOLD),
                    ft.TextField(label="検索", width=300),
                    ft.ElevatedButton("検索"),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=20,
            )

        elif destination_key == "settings":
            return ft.Column(
                [
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

        elif destination_key == "profile":
            return ft.Column(
                [
                    ft.Text("プロフィール画面", size=24, weight=ft.FontWeight.BOLD),
                    ft.TextField(label="ユーザー名", width=300),
                    ft.TextField(label="メールアドレス", width=300),
                    ft.ElevatedButton("保存"),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=20,
            )

        # デフォルトのコンテンツ
        return ft.Text(f"不明なDestination: {destination_key}", size=20)

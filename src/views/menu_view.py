"""
アプリケーションのメニュービュー
Fletを使用したAppBar、SideBar、コンテンツエリアを表示する基本的なレイアウト
"""

import flet as ft

from src.views.components.app_bar import AppBar
from src.views.components.side_bar import SideBar


class MenuView(ft.View):
    """
    アプリケーションのメインメニュービュー
    AppBar、SideBar、コンテンツエリアを含む基本的なレイアウト
    """

    def __init__(self, route="/"):
        super().__init__(
            route=route,
            appbar=AppBar(title=ft.Text("メニュー")),
            navigation_bar=SideBar(),
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # 各Destinationのコンテンツをキャッシュする辞書
        self.content_cache = {}

        # 現在選択されているDestination
        self.current_destination = None

        # コンテンツエリアのコンテナを作成
        self.content_container = ft.Container(
            content=ft.Text("メインコンテンツがここに表示されます", size=20),
            alignment=ft.alignment.center,
            expand=True,
        )

        # ビューのコンテンツを設定
        self.controls = [self.content_container]

        # SideBarのイベントハンドラを設定
        if isinstance(self.navigation_bar, SideBar):
            self.navigation_bar.on_destination_change = self.handle_destination_change

    def handle_destination_change(self, destination_key):
        """
        SideBarのDestination変更を処理する

        Args:
            destination_key: 選択されたDestinationのキー
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
        self.update_content(self.content_cache[destination_key])

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
                    ft.Text("ホーム画面", size=24),
                    ft.TextField(label="検索", width=300),
                    ft.ElevatedButton("検索"),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=20,
            )

        elif destination_key == "settings":
            return ft.Column(
                [
                    ft.Text("設定画面", size=24),
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
                    ft.Text("プロフィール画面", size=24),
                    ft.TextField(label="ユーザー名", width=300),
                    ft.TextField(label="メールアドレス", width=300),
                    ft.ElevatedButton("保存"),
                ],
                alignment=ft.MainAxisAlignment.START,
                spacing=20,
            )

        # デフォルトのコンテンツ
        return ft.Text(f"不明なDestination: {destination_key}", size=20)

    def update_content(self, new_content):
        """
        メインコンテンツエリアを更新する

        Args:
            new_content: 表示する新しいコンテンツ（Fletコントロール）
        """
        self.content_container.content = new_content
        self.update()


def create_menu_view(route=None, **kwargs):
    """MenuViewのインスタンスを作成して返す"""
    return MenuView(route=route or "/")


def main(page: ft.Page):
    """
    Fletアプリケーションのメインエントリーポイント
    """
    page.title = "MVVMアプリケーション"
    page.theme_mode = ft.ThemeMode.LIGHT

    menu_view = create_menu_view()
    page.add(menu_view)

    # 初期Destinationを設定
    if isinstance(menu_view.navigation_bar, SideBar):
        menu_view.handle_destination_change("home")


if __name__ == "__main__":
    ft.app(target=main)

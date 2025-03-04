import flet as ft

from src.core.router import Router
from src.views.menu_view import MenuView


def main(page: ft.Page):
    # ページの設定
    page.title = "Flet App"
    page.window.resizable = True

    # ルーターの初期化
    router = Router(page)

    # メニュービューをデフォルトルートとして追加
    router.add_route(path="/", view_class=MenuView, title="メニュー")

    # デフォルトルートに遷移
    router.navigate("/")


ft.app(target=main)

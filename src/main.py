"""
アプリケーションのメインエントリーポイント
Fletを使用してアプリケーションを起動します
"""

import flet as ft

from src.core.router import Router  # ルーターをインポート
from src.views.menu_view import create_menu_view


def main(page: ft.Page):
    """
    Fletアプリケーションのメインエントリーポイント
    """
    # ページの基本設定
    page.title = "FletApp"

    # ルーターの初期化
    router = Router(page)

    # ルートの設定
    router.add_route("/", create_menu_view, "Menu View")

    # 初期ルートに移動
    router.navigate("/")

    # ページの更新
    page.update()


if __name__ == "__main__":
    ft.app(target=main)

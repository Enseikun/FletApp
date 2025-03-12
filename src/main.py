"""
アプリケーションのメインエントリーポイント
"""

import flet as ft

from src.views.main_view import create_main_view


def main(page: ft.Page):
    """
    Fletアプリケーションのメインエントリーポイント
    """
    # ページの設定
    page.title = "TestApp"

    # MainViewにページを渡す
    main_view = create_main_view(page)

    # ページにビューを追加
    page.add(main_view)

    page.update()


if __name__ == "__main__":
    ft.app(target=main)

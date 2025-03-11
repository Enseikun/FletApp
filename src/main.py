"""
アプリケーションのメインエントリーポイント
"""

import flet as ft

from src.views.main_view import create_main_view


def main(page: ft.Page):
    """
    Fletアプリケーションのメインエントリーポイント
    """
    page.title = "シングルページアプリケーション"

    # メインビューを作成して追加
    main_view = create_main_view()
    page.add(main_view)


if __name__ == "__main__":
    ft.app(target=main)

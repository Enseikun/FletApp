"""
アプリケーションのメインエントリーポイント
"""

import flet as ft

from src.core.logger import get_logger
from src.views.components.progress_dialog import ProgressDialog
from src.views.main_view import create_main_view


def main(page: ft.Page):
    """
    Fletアプリケーションのメインエントリーポイント
    """
    # ロガーの初期化
    logger = get_logger()
    logger.info("アプリケーション起動")

    # ページの設定
    page.title = "ComSentry"

    # ProgressDialogの初期化
    progress_dialog = ProgressDialog()
    progress_dialog.initialize(page)
    logger.info("ProgressDialog初期化完了")

    # MainViewにページを渡す
    main_view = create_main_view(page)

    # ページにビューを追加
    page.add(main_view)

    page.update()
    logger.info("メインビュー初期化完了")


if __name__ == "__main__":
    ft.app(target=main)

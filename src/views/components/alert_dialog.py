"""
アラートダイアログコンポーネント
アプリケーション全体で使用する再利用可能なダイアログUIを提供
"""

import flet as ft

from src.core.logger import get_logger
from src.views.styles.style import AppTheme, Colors


class AlertDialog:
    """
    アラートダイアログコンポーネント
    アプリケーション全体で使用する再利用可能なダイアログUIを提供
    シングルトンパターンで実装
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AlertDialog, cls).__new__(cls)
            cls._instance._dialog = None
            cls._instance._page = None
            cls._instance._is_open = False
            cls._instance._current_dialog = None
            cls._instance.logger = get_logger()
        return cls._instance

    @property
    def is_open(self):
        """ダイアログが開いているかどうかを返す"""
        return self._is_open

    def initialize(self, page: ft.Page):
        """
        ダイアログの初期化
        Args:
            page (ft.Page): ダイアログを表示するページ
        """
        self._page = page
        self.logger.debug("AlertDialog: 初期化完了")

    def show_dialog(
        self, title, content, actions=None, modal=True, width=None, height=None
    ):
        """
        ダイアログを表示する
        Args:
            title (str): ダイアログのタイトル
            content (str): ダイアログの内容
            actions (list): ダイアログのアクション（ボタンなど）
            modal (bool): モーダルダイアログとして表示するかどうか
            width (int): ダイアログの幅
            height (int): ダイアログの高さ
        """
        if not self._page:
            self.logger.error(
                "ダイアログが初期化されていません。initialize()を呼び出してください。"
            )
            return

        # 前のダイアログが開いていれば閉じる
        self._close_current_dialog()

        # タイトルとコンテンツをft.Text型に変換
        title_control = title if isinstance(title, ft.Control) else ft.Text(title)
        content_control = (
            content if isinstance(content, ft.Control) else ft.Text(content)
        )

        # アクションが指定されていない場合はOKボタンを表示
        if not actions:
            actions = [
                ft.ElevatedButton(
                    text="OK",
                    on_click=lambda e: self.close_dialog(),
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=4),
                    ),
                ),
            ]

        # ダイアログを作成
        self._current_dialog = ft.AlertDialog(
            modal=modal,
            title=title_control,
            content=content_control,
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=4),
        )

        # 幅と高さを設定
        if width or height:
            container_content = content_control
            content_container = ft.Container(
                content=container_content,
                width=width,
                height=height,
            )
            self._current_dialog.content = content_container

        # ダイアログを表示
        self._is_open = True
        self._page.open(self._current_dialog)
        self._page.update()
        self.logger.debug("AlertDialog: ダイアログを表示しました")

    def show_confirmation_dialog(self, title, content, on_confirm, on_cancel=None):
        """
        確認ダイアログを表示する
        Args:
            title (str): ダイアログのタイトル
            content (str): ダイアログの内容
            on_confirm (function): 確認時のコールバック関数
            on_cancel (function): キャンセル時のコールバック関数
        """
        # アクションボタンを作成
        actions = [
            ft.TextButton(
                text="いいえ",
                on_click=lambda e: self._on_cancel_clicked(e, on_cancel),
                style=ft.ButtonStyle(
                    color=Colors.TEXT,
                ),
            ),
            ft.ElevatedButton(
                text="はい",
                on_click=lambda e: self._on_confirm_clicked(e, on_confirm),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=4),
                    color=Colors.TEXT_ON_ACTION,
                    bgcolor=Colors.ACTION,
                ),
            ),
        ]

        # ダイアログを表示
        self.show_dialog(title=title, content=content, actions=actions, modal=True)

    def show_error_dialog(self, title, content):
        """
        エラーダイアログを表示する
        Args:
            title (str): ダイアログのタイトル
            content (str): ダイアログの内容
        """
        # タイトルが指定されていない場合はデフォルトのタイトルを使用
        if not title:
            title = "エラー"

        # アクションボタンを作成
        actions = [
            ft.ElevatedButton(
                text="OK",
                on_click=lambda e: self.close_dialog(),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=4),
                ),
            ),
        ]

        # ダイアログを表示
        self.show_dialog(title=title, content=content, actions=actions, modal=True)

    def show_completion_dialog(self, title, content):
        """
        完了ダイアログを表示する
        Args:
            title (str): ダイアログのタイトル
            content (str): ダイアログの内容
        """
        # タイトルが指定されていない場合はデフォルトのタイトルを使用
        if not title:
            title = "完了"

        # アクションボタンを作成
        actions = [
            ft.ElevatedButton(
                text="OK",
                on_click=lambda e: self.close_dialog(),
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=4),
                ),
            ),
        ]

        # ダイアログを表示
        self.show_dialog(title=title, content=content, actions=actions, modal=True)

    def _on_confirm_clicked(self, e, on_confirm):
        """
        確認ボタンクリック時の処理
        Args:
            e (event): クリックイベント
            on_confirm (function): 確認時のコールバック関数
        """
        self.close_dialog()
        if on_confirm:
            on_confirm(e)

    def _on_cancel_clicked(self, e, on_cancel):
        """
        キャンセルボタンクリック時の処理
        Args:
            e (event): クリックイベント
            on_cancel (function): キャンセル時のコールバック関数
        """
        self.close_dialog()
        if on_cancel:
            on_cancel(e)

    def close_dialog(self):
        """
        現在開いているダイアログを閉じる
        """
        self._close_current_dialog()

    def _close_current_dialog(self):
        """
        現在開いているダイアログを閉じる（内部メソッド）
        """
        if self._is_open and self._current_dialog and self._page:
            self._page.close(self._current_dialog)
            self._current_dialog = None
            self._is_open = False
            self._page.update()
            self.logger.debug("AlertDialog: ダイアログを閉じました")

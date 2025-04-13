"""
アラートダイアログコンポーネント
シングルトンパターンで実装されたダイアログUIを提供
"""

import asyncio

import flet as ft

from src.views.styles.style import AppTheme, Colors


class ProgressDialog:
    """
    プログレスバー付きダイアログコンポーネント
    処理の進行状況を表示するためのダイアログUIを提供
    シングルトンパターンで実装
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProgressDialog, cls).__new__(cls)
            cls._instance._dialog = None
            cls._instance._page = None
            cls._instance._progress_bar = None
            cls._instance._is_open = False
        return cls._instance

    def initialize(self, page: ft.Page):
        """
        ダイアログの初期化
        Args:
            page (ft.Page): ダイアログを表示するページ
        """
        self._page = page
        self._progress_bar = ft.ProgressBar(
            color=Colors.PRIMARY,
            bgcolor="#eeeeee",
        )

        self._content_column = ft.Column(
            controls=[
                ft.Text(""),  # メッセージ用テキスト
                self._progress_bar,
            ],
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self._dialog = ft.AlertDialog(
            title=ft.Text(""),
            content=ft.Container(
                content=self._content_column,
                height=40,  # 高さのみ固定
                # 幅は指定せず、テキストに応じて自動調整
            ),
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=4),
        )

    async def show_async(
        self,
        title: str,
        content: str,
        current_value: float = 0,
        max_value: float = None,
    ):
        """
        ダイアログを非同期で表示
        Args:
            title (str): ダイアログのタイトル
            content (str): ダイアログの内容
            current_value (float): 現在の進捗値
            max_value (float): 進捗の最大値（Noneの場合はIndeterminate mode）
        """
        if not self._dialog or not self._page:
            raise RuntimeError(
                "ダイアログが初期化されていません。initialize()を呼び出してください。"
            )

        self._dialog.title.value = title
        self._content_column.controls[0].value = content

        # ProgressBarの状態を設定
        if max_value is not None and max_value > 0:
            # 0.0から1.0の範囲に正規化する
            self._progress_bar.value = current_value / max_value
        else:
            # 不確定モード
            self._progress_bar.value = None

        # ダイアログを表示
        self._page.open(self._dialog)
        self._is_open = True
        self._page.update()  # 同期版を使用

    async def update_progress_async(self, current_value: float, max_value: float):
        """
        進捗状況を非同期で更新
        Args:
            current_value (float): 現在の進捗値
            max_value (float): 進捗の最大値（0の場合はIndeterminate mode）
        """
        if max_value > 0:
            # 0.0から1.0の範囲に正規化する
            self._progress_bar.value = current_value / max_value
        else:
            self._progress_bar.value = None

        if self._page and self._is_open:
            self._page.update()  # 同期版を使用

    async def close_async(self):
        """
        ダイアログを非同期で閉じる
        """
        if self._is_open:
            self._page.close(self._dialog)
            self._is_open = False
            self._page.update()  # 同期版を使用

    def _close_dialog(self, e):
        """
        ダイアログを閉じる（同期版）
        """
        self._page.close(self._dialog)
        self._is_open = False
        self._page.update()

    # 後方互換性のための同期メソッド
    def show(
        self, title: str, content: str, current_value: float = 0, max_value: float = 0
    ):
        """
        ダイアログを表示（同期版）
        """
        if not self._dialog or not self._page:
            raise RuntimeError(
                "ダイアログが初期化されていません。initialize()を呼び出してください。"
            )

        self._dialog.title.value = title
        self._content_column.controls[0].value = content

        if max_value > 0:
            # 0.0から1.0の範囲に正規化する
            self._progress_bar.value = current_value / max_value
        else:
            # 不確定モード
            self._progress_bar.value = None

        # ダイアログを表示
        self._page.open(self._dialog)
        self._is_open = True
        self._page.update()

    def update_progress(self, current_value: float, max_value: float):
        """
        進捗状況を更新（同期版）
        """
        if max_value > 0:
            # 0.0から1.0の範囲に正規化する
            self._progress_bar.value = current_value / max_value
        else:
            self._progress_bar.value = None

        if self._page and self._is_open:
            self._page.update()

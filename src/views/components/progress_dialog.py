"""
アラートダイアログコンポーネント
シングルトンパターンで実装されたダイアログUIを提供
"""

import asyncio
import logging

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
            cls._instance._close_button = None
            cls._instance._button_clicked = asyncio.Event()
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

        # ボタン用のコンテナ（初期状態では非表示）
        self._button_container = ft.Container(
            content=ft.Row(
                controls=[],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            visible=False,
            margin=ft.margin.only(top=10),
        )

        # メッセージとプログレスバーの後にボタンコンテナを追加
        self._content_column.controls.append(self._button_container)

        self._dialog = ft.AlertDialog(
            title=ft.Text(""),
            content=ft.Container(
                content=self._content_column,
                # width=400,
                height=40,
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
        # UI更新後に少し待機して描画が完了する余地を与える
        await asyncio.sleep(0.05)

    async def update_progress_async(self, current_value: float, max_value: float):
        """
        進捗状況を非同期で更新
        Args:
            current_value (float): 現在の進捗値
            max_value (float): 進捗の最大値（0の場合はIndeterminate mode）
        """
        # ログ追加：設定前の値
        prev_value = self._progress_bar.value

        if max_value > 0:
            # 0.0から1.0の範囲に正規化する
            normalized_value = current_value / max_value
            self._progress_bar.value = normalized_value

            # ログ追加：設定後の値
            logger = logging.getLogger("flet_app")
            logger.debug(
                f"ProgressDialog: プログレスバー更新 (Linerモード) - 前={prev_value}, "
                f"新={normalized_value} (値={current_value}/{max_value})"
            )
        else:
            self._progress_bar.value = None

            # ログ追加：Indeterminateモードに設定
            logger = logging.getLogger("flet_app")
            logger.debug(
                f"ProgressDialog: プログレスバー更新 (Indeterminateモード) - 前={prev_value}"
            )

        if self._page and self._is_open:
            self._page.update()  # 同期版を使用
            # UI更新後に少し待機して描画が完了する余地を与える
            await asyncio.sleep(0.02)

    async def close_async(self):
        """
        ダイアログを非同期で閉じる
        """
        if self._is_open:
            self._page.close(self._dialog)
            self._is_open = False
            self._page.update()  # 同期版を使用
            # UI更新後に少し待機して描画が完了する余地を与える
            await asyncio.sleep(0.05)

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

    async def update_message_async(self, content: str):
        """
        ダイアログのメッセージを非同期で更新
        Args:
            content (str): 新しいダイアログの内容
        """
        if not self._dialog or not self._page:
            raise RuntimeError(
                "ダイアログが初期化されていません。initialize()を呼び出してください。"
            )

        if self._is_open:
            self._content_column.controls[0].value = content
            self._page.update()  # 同期版を使用
            # UI更新後に少し待機して描画が完了する余地を与える
            await asyncio.sleep(0.02)

    async def add_close_button_async(self, button_text: str = "OK"):
        """
        閉じるボタンを非同期で追加
        Args:
            button_text (str): ボタンのテキスト
        """
        if not self._dialog or not self._page:
            raise RuntimeError(
                "ダイアログが初期化されていません。initialize()を呼び出してください。"
            )

        if not self._is_open:
            return

        # イベントをリセット
        self._button_clicked.clear()

        # ボタンのクリックハンドラ
        def on_button_click(e):
            # ボタンがクリックされたらイベントをセット
            asyncio.create_task(self._set_button_clicked())

        # ボタンを作成
        self._close_button = ft.ElevatedButton(
            text=button_text,
            on_click=on_button_click,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=4),
            ),
        )

        # ボタンコンテナにボタンを追加
        row = self._button_container.content
        row.controls = [self._close_button]
        self._button_container.visible = True

        # UI更新
        self._page.update()
        # UI更新後に少し待機して描画が完了する余地を与える
        await asyncio.sleep(0.05)

    async def _set_button_clicked(self):
        """内部メソッド: ボタンがクリックされたことを記録"""
        self._button_clicked.set()

    async def wait_for_close(self, timeout: float = None):
        """
        ユーザーがボタンをクリックするまで待機
        Args:
            timeout (float): タイムアウト時間（秒）。Noneの場合は無限に待機

        Returns:
            bool: タイムアウトせずにボタンがクリックされたかどうか
        """
        try:
            await asyncio.wait_for(self._button_clicked.wait(), timeout)
            # ボタンクリック後にダイアログを閉じる
            await self.close_async()
            return True
        except asyncio.TimeoutError:
            return False

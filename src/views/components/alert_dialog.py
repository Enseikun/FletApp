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
        print(f"AlertDialog: show_dialogが呼び出されました - title: {title}")

        if not self._page:
            error_msg = (
                "ダイアログが初期化されていません。initialize()を呼び出してください。"
            )
            self.logger.error(error_msg)
            print(f"AlertDialog: {error_msg}")

            # 自動初期化を試みる
            if hasattr(self, "page") and self.page:
                print("AlertDialog: 自動初期化を試みます")
                self.initialize(self.page)
            else:
                print(
                    "AlertDialog: 自動初期化できません - pageオブジェクトがありません"
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
        try:
            self._current_dialog = ft.AlertDialog(
                modal=modal,
                title=title_control,
                content=content_control,
                actions=actions,
                actions_alignment=ft.MainAxisAlignment.END,
                shape=ft.RoundedRectangleBorder(radius=4),
                on_dismiss=lambda e: self.logger.debug(
                    "AlertDialog: ダイアログが閉じられました"
                ),
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

            # 公式ドキュメントに従ってpage.open()を使用してダイアログを表示
            self._is_open = True

            # ページが有効かチェック
            if self._page:
                print("AlertDialog: ダイアログを表示します")
                self._page.open(self._current_dialog)
                self._page.update()
                self.logger.debug("AlertDialog: ダイアログを表示しました")
                print("AlertDialog: ダイアログ表示が完了しました")
            else:
                print(
                    "AlertDialog: ページオブジェクトがないためダイアログを表示できません"
                )

        except Exception as e:
            error_msg = f"AlertDialog: ダイアログ表示中にエラー発生 - {str(e)}"
            self.logger.error(error_msg)
            print(error_msg)
            # 重大なエラーの場合は状態をリセット
            self._is_open = False
            self._current_dialog = None

    def show_confirmation_dialog(self, title, content, on_confirm, on_cancel=None):
        """
        確認ダイアログを表示する
        Args:
            title (str): ダイアログのタイトル
            content (str): ダイアログの内容
            on_confirm (function): 確認時のコールバック関数
            on_cancel (function): キャンセル時のコールバック関数
        """
        print(
            f"AlertDialog: show_confirmation_dialogが呼び出されました - title: {title}"
        )

        # ページの初期化確認
        if not self._page and hasattr(self, "page"):
            print("AlertDialog: ページが未初期化、did_mountの前に初期化を実行します")
            self.initialize(self.page)

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
        try:
            print("AlertDialog: show_dialogを呼び出します")
            self.show_dialog(title=title, content=content, actions=actions, modal=True)
            print("AlertDialog: show_dialogの呼び出しが完了しました")
        except Exception as e:
            print(f"AlertDialog: show_dialogでエラーが発生しました - {str(e)}")
            self.logger.error(f"AlertDialog: show_dialogでエラー発生 - {str(e)}")
            # エラーが発生した場合、フォールバック処理
            if self._page:
                try:
                    self._page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"エラー: {str(e)}"), bgcolor=ft.colors.RED_400
                    )
                    self._page.snack_bar.open = True
                    self._page.update()
                except Exception:
                    print("AlertDialog: フォールバック処理にも失敗しました")

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
            # 公式ドキュメントに従ってpage.close()を使用
            self._page.close(self._current_dialog)

            # ダイアログへの参照をクリア
            self._current_dialog = None
            self._is_open = False
            self._page.update()
            self.logger.debug("AlertDialog: ダイアログを閉じました")

    def did_mount(self):
        """コンポーネントがマウントされた時の処理"""
        print("AlertDialog: did_mountが呼び出されました")
        if self._page is None and hasattr(self, "page"):
            print(f"AlertDialog: did_mountでpageオブジェクトを検出: {self.page}")
            self.initialize(self.page)
            self.logger.debug("AlertDialog: did_mountで自動初期化しました")
            print("AlertDialog: did_mountで自動初期化しました")
        else:
            print(
                f"AlertDialog: pageオブジェクトの状態 - self._page: {self._page}, hasattr(self, 'page'): {hasattr(self, 'page')}"
            )

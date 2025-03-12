"""
コンポーネントの基底クラス
すべてのカスタムUIコンポーネントの基盤となるクラス
"""

from typing import Callable, Optional

import flet as ft

from src.views.styles.style import ComponentState, ComponentStyle, StyleManager


class BaseComponent(ft.Control):
    """
    すべてのコンポーネントの基底クラス
    Fletのコントロールを拡張し、状態管理やスタイル適用の機能を提供します
    """

    def __init__(
        self,
        text: str = "",
        enabled: bool = True,
        enable_hover: bool = True,
        enable_press: bool = True,
        activate: bool = False,
        on_click_callback: Optional[Callable] = None,
    ):
        """
        BaseComponentの初期化

        Args:
            text: コンポーネントに表示するテキスト
            enabled: コンポーネントが有効かどうか
            enable_hover: ホバー効果を有効にするかどうか
            enable_press: プレス効果を有効にするかどうか
            activate: アクティブ状態で初期化するかどうか
            on_click_callback: クリックイベントのコールバック関数
        """
        super().__init__()
        self.text = text
        self._enabled = enabled
        self._enable_hover = enable_hover
        self._enable_press = enable_press
        self.on_click_callback = on_click_callback

        # 初期状態の設定
        if not enabled:
            self._state = ComponentState.DISABLED
        elif activate:
            self._state = ComponentState.ACTIVE
        else:
            self._state = ComponentState.NORMAL

        # 各状態に対応するスタイル情報
        self._styles = StyleManager.get_default_styles()

    def _get_current_style(self) -> ComponentStyle:
        """現在の状態に対応するスタイルを取得"""
        return self._styles[self._state]

    def _create_content(self):
        """コンポーネントのコンテンツを作成（継承先でオーバーライド可能）"""
        return ft.Text(self.text, color=self._get_current_style().text_color)

    def _create_container(self) -> ft.Container:
        """スタイルが適用されたコンテナを作成"""
        style = self._get_current_style().to_dict()

        # イベントハンドラの設定
        handlers = {}
        if self._enable_hover:
            handlers["on_hover"] = self._on_hover
        if self._enable_press:
            handlers["on_click"] = self._on_click

        container = ft.Container(
            content=self._create_content(),
            **handlers,
            **style,
        )

        return container

    def _on_hover(self, e):
        """ホバーイベントのハンドラ"""
        if not self._enabled or not self._enable_hover:
            return

        self._state = (
            ComponentState.HOVERED if e.data == "true" else ComponentState.NORMAL
        )
        self.update()

    def _on_click(self, e):
        """クリックイベントのハンドラ"""
        if not self._enabled or not self._enable_press:
            return

        self._state = ComponentState.PRESSED
        self.update()

        # コールバックが設定されている場合は呼び出す
        if self.on_click_callback and self._enabled:
            self.on_click_callback(e)

        # クリック後に通常状態に戻す（プレス状態を維持しない）
        if self._enabled:
            self._state = (
                self._state
                if self._state == ComponentState.ACTIVE
                else ComponentState.NORMAL
            )
            self.update()

    def enable(self):
        """コンポーネントを有効化"""
        self._enabled = True
        self._state = ComponentState.NORMAL
        self.update()

    def disable(self):
        """コンポーネントを無効化"""
        self._enabled = False
        self._state = ComponentState.DISABLED
        self.update()

    def activate(self):
        """コンポーネントをアクティブ状態に設定"""
        if not self._enabled:
            return
        self._state = ComponentState.ACTIVE
        self.update()

    def deactivate(self):
        """コンポーネントを非アクティブ状態に設定"""
        if not self._enabled:
            return
        self._state = ComponentState.NORMAL
        self.update()

    def set_error(self, has_error: bool = True):
        """エラー状態を設定"""
        if not self._enabled:
            return

        if has_error:
            self._state = ComponentState.ERROR
        else:
            self._state = ComponentState.NORMAL
        self.update()

    def build(self):
        """コンポーネントのUIを構築"""
        return self._create_container()

    def _get_control_name(self):
        # クラス名をスネークケースに変換して返す
        class_name = self.__class__.__name__
        return "".join(
            ["_" + c.lower() if c.isupper() else c for c in class_name]
        ).lstrip("_")

"""
コンポーネントの基底クラス
Fletのコントロールを拡張した基本機能を提供します
"""

from enum import Enum
from typing import Any, Dict, Optional

import flet as ft

from src.views.styles.color import Colors


class ComponentState(str, Enum):
    """コンポーネントの状態を表す列挙型"""

    NORMAL = "normal"
    DISABLED = "disabled"
    HOVERED = "hovered"
    FOCUSED = "focused"
    PRESSED = "pressed"


class ComponentStyle:
    """コンポーネントのスタイル情報を保持するクラス"""

    def __init__(self):
        """スタイル情報の初期化"""
        self.background_color = Colors.BACKGROUND
        self.text_color = Colors.TEXT_PRIMARY
        self.border_color = Colors.BORDER
        self.padding = 8
        self.margin = 0
        self.border_width = 1
        self.border_radius = 4
        self.opacity = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """スタイル情報を辞書形式で返す"""
        return {
            "bgcolor": self.background_color,
            "color": self.text_color,
            "border_color": self.border_color,
            "padding": self.padding,
            "margin": self.margin,
            "border_width": self.border_width,
            "border_radius": self.border_radius,
            "opacity": self.opacity,
        }


class BaseComponent(ft.Control):
    """
    すべてのコンポーネントの基底クラス
    Fletのコントロールを拡張し、状態管理やスタイル適用の機能を提供します
    """

    def __init__(self, text: str = "", enabled: bool = True):
        """
        BaseComponentの初期化

        Args:
            text: コンポーネントに表示するテキスト
            enabled: コンポーネントが有効かどうか
        """
        super().__init__()
        self.text = text
        self._enabled = enabled
        self._state = ComponentState.NORMAL if enabled else ComponentState.DISABLED

        # 各状態に対応するスタイル情報
        self._styles: Dict[ComponentState, ComponentStyle] = {
            state: ComponentStyle() for state in ComponentState
        }

        # 無効状態のスタイルを設定
        self._styles[ComponentState.DISABLED].opacity = 0.5
        self._styles[ComponentState.DISABLED].text_color = Colors.TEXT_DISABLED

    def _get_current_style(self) -> ComponentStyle:
        """現在の状態に対応するスタイルを取得"""
        return self._styles[self._state]

    def _create_container(self) -> ft.Container:
        """スタイルが適用されたコンテナを作成"""
        style = self._get_current_style().to_dict()

        container = ft.Container(
            content=ft.Text(self.text),
            on_hover=self._on_hover,
            on_click=self._on_click,
            **style,
        )

        return container

    def _on_hover(self, e):
        """ホバーイベントのハンドラ"""
        if not self._enabled:
            return

        self._state = (
            ComponentState.HOVERED if e.data == "true" else ComponentState.NORMAL
        )
        self.update()

    def _on_click(self, e):
        """クリックイベントのハンドラ"""
        if not self._enabled:
            return

        self._state = ComponentState.PRESSED
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

    def is_enabled(self) -> bool:
        """コンポーネントが有効かどうかを返す"""
        return self._enabled

    def build(self):
        """
        コンポーネントのUIを構築
        サブクラスでオーバーライドする必要があります
        """
        return self._create_container()

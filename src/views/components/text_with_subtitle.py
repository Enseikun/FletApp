"""
テキストとサブテキストを2行で表示するコンポーネント
"""

from typing import Callable, Optional

import flet as ft

from src.views.components.mixins.event_handling_mixin import EventHandlingMixin
from src.views.components.mixins.state_management_mixin import StateManagementMixin
from src.views.components.mixins.ui_component_mixin import UIComponentMixin
from src.views.styles.style import ComponentState, ComponentStyle, StyleManager


class TextWithSubtitle(
    ft.Container, StateManagementMixin, UIComponentMixin, EventHandlingMixin
):
    """
    メインテキストとサブテキストを2行で表示するコンポーネント
    クリック可能で、コールバック機能を持ちます
    """

    def __init__(self, text: str, subtitle: str, **kwargs):
        """
        TextWithSubtitleの初期化

        Args:
            text: メインテキスト
            subtitle: サブテキスト
            **kwargs: その他のキーワード引数
        """
        super().__init__()
        self.text = text
        self.subtitle = subtitle
        self.init_state_management(**kwargs)
        self._setup_container()

    def _create_content(self):
        """コンポーネントのコンテンツを作成"""
        style = self._get_current_style()

        return ft.Column(
            spacing=4,
            controls=[
                ft.Text(
                    self.text,
                    color=style.text_color,
                    size=16,
                    weight="bold",
                ),
                ft.Text(
                    self.subtitle,
                    color=style.text_color,
                    size=14,
                    opacity=0.8,
                ),
            ],
        )

    def _setup_container(self):
        """コンテナの設定を行う"""
        # スタイルの適用
        style = self._get_current_style().to_dict()
        for key, value in style.items():
            setattr(self, key, value)

        # コンテンツの設定
        self.content = self._create_content()

        # イベントハンドラの設定
        if self._enable_hover:
            self.on_hover = self._on_hover
        if self._enable_press:
            self.on_click = self._on_click

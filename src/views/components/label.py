"""
テキストを表示するためのラベルコンポーネント
"""

from typing import Optional

import flet as ft

from src.views.components.mixins.event_handling_mixin import EventHandlingMixin
from src.views.components.mixins.state_management_mixin import StateManagementMixin
from src.views.components.mixins.ui_component_mixin import UIComponentMixin
from src.views.styles.color import Colors
from src.views.styles.style import ComponentState


class Label(ft.Container, StateManagementMixin, UIComponentMixin, EventHandlingMixin):
    """
    テキストを表示するためのラベルコンポーネント
    """

    def __init__(
        self,
        text: str = "",
        font_size: float = 14,
        bold: bool = False,
        italic: bool = False,
        text_align: str = "left",
        selectable: bool = False,
        **kwargs,
    ):
        """
        Labelの初期化

        Args:
            text: 表示するテキスト
            font_size: フォントサイズ
            bold: 太字にするかどうか
            italic: 斜体にするかどうか
            text_align: テキストの配置（"left", "center", "right"）
            selectable: テキストを選択可能にするかどうか
            **kwargs: StateManagementMixinに渡す追加のパラメータ
        """
        super().__init__()

        # プロパティの設定
        self.text = text
        self._font_size = font_size
        self._bold = bold
        self._italic = italic
        self._text_align = text_align
        self._selectable = selectable

        # 状態管理の初期化
        self.init_state_management(**kwargs)

        # スタイルのカスタマイズ
        self._customize_styles()

        # コンテナの設定
        self._setup_container()

    def _customize_styles(self):
        """ラベル用のスタイルをカスタマイズ"""
        # 共通のスタイル設定
        for state in ComponentState:
            self._styles[state].padding = 4
            self._styles[state].margin = 2

        # 状態別のスタイル設定
        self._styles[ComponentState.NORMAL].text_color = Colors.TEXT
        self._styles[ComponentState.HOVERED].text_color = Colors.TEXT_SECONDARY
        self._styles[ComponentState.FOCUSED].text_color = Colors.PRIMARY
        self._styles[ComponentState.PRESSED].text_color = Colors.PRIMARY_DARK

    def _create_content(self) -> ft.Control:
        """ラベルのコンテンツを作成"""
        # フォントウェイトの設定
        weight = ft.FontWeight.BOLD if self._bold else ft.FontWeight.NORMAL

        # フォントスタイルの設定
        style = ft.FontStyle.ITALIC if self._italic else ft.FontStyle.NORMAL

        # テキスト配置の設定
        text_align_map = {
            "left": ft.TextAlign.LEFT,
            "center": ft.TextAlign.CENTER,
            "right": ft.TextAlign.RIGHT,
        }
        text_align = text_align_map.get(self._text_align, ft.TextAlign.LEFT)

        # テキストコントロールの作成
        return ft.Text(
            value=self.text,
            size=self._font_size,
            weight=weight,
            italic=self._italic,
            text_align=text_align,
            selectable=self._selectable,
            color=self._get_current_style().text_color,
        )

    def build(self) -> ft.Control:
        """
        ラベルのUIを構築

        Returns:
            構築されたFletコントロール
        """
        return self._create_container()

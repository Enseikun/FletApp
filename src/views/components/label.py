from typing import Optional

import flet as ft

from src.views.components.base_component import BaseComponent, ComponentState
from src.views.styles.color import Colors


class Label(BaseComponent):
    """
    テキストを表示するためのラベルコンポーネント
    BaseComponentを継承し、Fletのテキスト表示機能を提供します
    """

    def __init__(
        self,
        text: str = "",
        font_size: float = 14,
        bold: bool = False,
        italic: bool = False,
        enabled: bool = True,
        text_align: str = "left",
        selectable: bool = False,
    ):
        """
        Labelの初期化

        Args:
            text: 表示するテキスト
            font_size: フォントサイズ
            bold: 太字にするかどうか
            italic: 斜体にするかどうか
            enabled: 有効かどうか
            text_align: テキストの配置（"left", "center", "right"）
            selectable: テキストを選択可能にするかどうか
        """
        super().__init__(text=text, enabled=enabled)

        self._font_size = font_size
        self._bold = bold
        self._italic = italic
        self._text_align = text_align
        self._selectable = selectable

        # ラベル用のスタイル設定
        for state in ComponentState:
            self._styles[state].padding = 4
            self._styles[state].margin = 2

        # 通常状態のスタイル
        self._styles[ComponentState.NORMAL].text_color = Colors.TEXT

        # ホバー状態のスタイル
        self._styles[ComponentState.HOVERED].text_color = Colors.TEXT_SECONDARY

        # フォーカス状態のスタイル
        self._styles[ComponentState.FOCUSED].text_color = Colors.PRIMARY

        # 押下状態のスタイル
        self._styles[ComponentState.PRESSED].text_color = Colors.PRIMARY_DARK

    def build(self) -> ft.Control:
        """
        ラベルのUIを構築

        Returns:
            構築されたFletコントロール
        """
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
        text_control = ft.Text(
            value=self.text,
            size=self._font_size,
            weight=weight,
            italic=self._italic,
            text_align=text_align,
            selectable=self._selectable,
        )

        # スタイルを適用したコンテナに配置
        container = ft.Container(
            content=text_control,
            on_hover=lambda e: self.set_state(
                ComponentState.HOVERED if e.data == "true" else ComponentState.NORMAL
            ),
        )

        return self.apply_style_to_control(container)

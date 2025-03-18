"""
テキストとサブテキストを2行で表示し、右端に削除アイコンを持つコンポーネント
"""

from typing import Callable, Optional

import flet as ft

from src.views.components.mixins.event_handling_mixin import EventHandlingMixin
from src.views.components.mixins.state_management_mixin import StateManagementMixin
from src.views.components.mixins.ui_component_mixin import UIComponentMixin
from src.views.components.text_with_subtitle import TextWithSubtitle
from src.views.styles.style import ComponentState, ComponentStyle, StyleManager


class TextWithSubtitleWithDeleteIcon(TextWithSubtitle):
    """
    メインテキストとサブテキストを2行で表示し、右端に削除アイコンを持つコンポーネント
    クリック可能で、コールバック機能を持ちます
    """

    def __init__(
        self,
        text: str,
        subtitle: str,
        on_delete_callback=None,
        on_click_callback=None,
        text_weight="normal",
        enable_press=False,
        **kwargs,
    ):
        """
        TextWithSubtitleWithDeleteIconの初期化

        Args:
            text: メインテキスト
            subtitle: サブテキスト
            on_delete_callback: 削除アイコンクリック時のコールバック関数
            on_click_callback: コンポーネントクリック時のコールバック関数
            text_weight: テキストの太さ
            enable_press: クリック可能かどうか
            **kwargs: その他のキーワード引数
        """
        self.on_delete_callback = on_delete_callback
        super().__init__(
            text=text,
            subtitle=subtitle,
            on_click_callback=on_click_callback,
            text_weight=text_weight,
            enable_press=enable_press,
            **kwargs,
        )

    def _setup_container(self):
        """コンテナの設定を行う"""
        # スタイルの適用
        style = self._get_current_style().to_dict()
        for key, value in style.items():
            setattr(self, key, value)

        # 削除アイコンの作成
        delete_icon = ft.IconButton(
            icon=ft.icons.DELETE,
            icon_color=style.get("text_color"),
            on_click=self._on_delete_click,
            tooltip="削除",
        )

        # コンテンツの設定
        self.content = ft.Row(
            controls=[
                self._create_content(),
                delete_icon,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            expand=True,
        )

        # イベントハンドラの設定
        if self._enable_hover:
            self.on_hover = self._on_hover
        if self._enable_press:
            self.on_click = self._on_click

    def _on_delete_click(self, e):
        """削除アイコンクリック時の処理"""
        if self.on_delete_callback:
            self.on_delete_callback(e)
        # イベントの伝播を停止
        e.control.page.update()

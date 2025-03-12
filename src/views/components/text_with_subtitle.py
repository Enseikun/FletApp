"""
テキストとサブテキストを2行で表示するコンポーネント
"""

from typing import Callable, Optional

import flet as ft

from src.views.components.base_component import BaseComponent


class TextWithSubtitle(BaseComponent):
    """
    メインテキストとサブテキストを2行で表示するコンポーネント
    クリック可能で、コールバック機能を持ちます
    """

    def __init__(
        self,
        text: str = "",
        subtitle: str = "",
        on_click_callback: Optional[Callable] = None,
        enabled: bool = True,
        enable_hover: bool = True,
        enable_press: bool = True,
        activate: bool = False,
    ):
        """
        TextWithSubtitleの初期化

        Args:
            text: メインテキスト
            subtitle: サブテキスト
            on_click_callback: クリック時に呼び出されるコールバック関数
            enabled: コンポーネントが有効かどうか
            enable_hover: ホバー効果を有効にするかどうか
            enable_press: プレス効果を有効にするかどうか
            activate: アクティブ状態で初期化するかどうか
        """
        super().__init__(
            text=text,
            enabled=enabled,
            enable_hover=enable_hover,
            enable_press=enable_press,
            activate=activate,
            on_click_callback=on_click_callback,
        )
        self.subtitle = subtitle

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

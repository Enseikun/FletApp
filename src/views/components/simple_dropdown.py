"""
シンプルなドロップダウンコンポーネント
Fletの標準機能を活用した実装
"""

from typing import Callable, List, Optional, Union

import flet as ft


class SimpleDropdown(ft.Container):
    """
    シンプルなドロップダウンコンポーネント
    Fletの標準機能を活用した実装
    """

    def __init__(
        self,
        options: List[Union[str, tuple[str, str]]],
        icon: Optional[str] = None,
        on_change: Optional[Callable] = None,
        **kwargs,
    ):
        """
        SimpleDropdownの初期化

        Args:
            options: ドロップダウンの選択肢リスト（文字列または(値, 表示名)のタプル）
            icon: 表示するアイコン名
            on_change: 値変更時のコールバック関数
            **kwargs: その他のキーワード引数
        """
        super().__init__()

        # ドロップダウンの選択肢を作成
        dropdown_options = []
        for option in options:
            if isinstance(option, tuple) and len(option) == 2:
                # (値, 表示名)の形式
                dropdown_options.append(
                    ft.dropdownm2.Option(key=option[0], text=option[1])
                )
            else:
                # 文字列の形式
                dropdown_options.append(ft.dropdownm2.Option(key=option, text=option))

        # デフォルトのスタイル設定
        default_style = {
            "expand": True,
            "color": ft.colors.ON_SURFACE,
            "filled": True,
            "border_radius": 8,
            "content_padding": 10,
            "hint_text": "選択してください",
            "label_style": ft.TextStyle(size=14),
            "text_style": ft.TextStyle(size=14),
        }

        # デフォルトのスタイルとユーザー指定のスタイルをマージ
        style = {**default_style, **kwargs}

        # ドロップダウンの作成
        self.dropdown = ft.DropdownM2(
            options=dropdown_options, on_change=on_change, **style
        )

        # アイコンがある場合は、Rowでラップ
        if icon:
            self.icon = ft.Icon(
                name=icon,
                size=24,
                color=style.get("color", ft.colors.ON_SURFACE),
            )
            self.content = ft.Row(
                controls=[self.icon, self.dropdown],
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            )
        else:
            self.content = self.dropdown

        # コンテナの設定
        self.expand = True

    def update_options(self, new_options: List[Union[str, tuple[str, str]]]):
        """
        ドロップダウンの選択肢を更新

        Args:
            new_options: 新しい選択肢リスト
        """
        dropdown_options = []
        for option in new_options:
            if isinstance(option, tuple) and len(option) == 2:
                dropdown_options.append(
                    ft.dropdownm2.Option(key=option[0], text=option[1])
                )
            else:
                dropdown_options.append(ft.dropdownm2.Option(key=option, text=option))

        self.dropdown.options = dropdown_options
        self.dropdown.update()

    def set_value(self, value: str):
        """
        値を設定

        Args:
            value: 設定する値
        """
        self.dropdown.value = value
        self.dropdown.update()

    @property
    def value(self):
        """現在の値を取得"""
        return self.dropdown.value

    @value.setter
    def value(self, value: str):
        """値を設定"""
        self.set_value(value)

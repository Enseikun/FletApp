"""
アイコンとドロップダウンを組み合わせたコンポーネント
"""

from typing import Callable, List, Optional, Tuple, Union

import flet as ft

from src.views.components.mixins.event_handling_mixin import EventHandlingMixin
from src.views.components.mixins.state_management_mixin import StateManagementMixin
from src.views.components.mixins.ui_component_mixin import UIComponentMixin
from src.views.styles.style import ComponentState


class IconDropdown(
    ft.Container, StateManagementMixin, UIComponentMixin, EventHandlingMixin
):
    """
    アイコンとドロップダウンを組み合わせたコンポーネント
    左側にアイコン、右側にドロップダウンを配置
    """

    def __init__(
        self,
        icon: str,
        options: List[Union[str, Tuple[str, str]]],
        on_change: Optional[Callable] = None,
        **kwargs,
    ):
        """
        IconDropdownの初期化

        Args:
            icon: 表示するアイコン名
            options: ドロップダウンの選択肢リスト（文字列または(値, 表示名)のタプル）
            on_change: 値変更時のコールバック関数
            **kwargs: その他のキーワード引数
        """
        super().__init__()

        # プロパティの設定
        self.icon_name = icon
        self.icon_color = None  # スタイルから自動設定
        self.icon_size = 24  # 固定サイズ
        self.options = options
        self.value = None  # 初期状態では未選択
        self.on_change_callback = on_change

        # 状態管理の初期化
        self.init_state_management(**kwargs)

        # コンテナの設定
        self._setup_container()
        self.expand = True

    def _create_dropdown_options(self):
        """ドロップダウンの選択肢を作成"""
        dropdown_options = []

        for option in self.options:
            if isinstance(option, tuple) and len(option) == 2:
                # (値, 表示名)の形式
                dropdown_options.append(
                    ft.dropdownm2.Option(key=option[0], text=option[1])
                )
            else:
                # 文字列の形式
                dropdown_options.append(ft.dropdownm2.Option(key=option, text=option))

        return dropdown_options

    def _on_dropdown_change(self, e):
        """ドロップダウンの値変更時のハンドラ"""
        self.value = e.control.value

        if self.on_change_callback and self._enabled:
            # イベントオブジェクトを作成して親コンポーネントに渡す
            e.control = self
            self.on_change_callback(e)

    def _create_content(self):
        """コンポーネントのコンテンツを作成"""
        style = self._get_current_style()

        # アイコンの色を設定
        icon_color = self.icon_color if self.icon_color else style.text_color

        # アイコン
        icon = ft.Icon(
            name=self.icon_name,
            size=self.icon_size,
            color=icon_color,
        )

        # ドロップダウン
        dropdown = ft.DropdownM2(
            options=self._create_dropdown_options(),
            value=self.value,
            on_change=self._on_dropdown_change,
            disabled=not self._enabled,
            expand=True,
            color=style.text_color,
            filled=True,
            border_radius=8,
            content_padding=10,
            hint_text="選択してください",
            label_style=ft.TextStyle(size=14),
            text_style=ft.TextStyle(size=14),
        )

        # 行レイアウトでアイコンとドロップダウンを配置
        return ft.Row(
            controls=[
                icon,
                dropdown,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )

    def _setup_container(self):
        """コンテナの設定を行う"""
        # スタイルの適用
        style = self._get_current_style().to_dict()
        for key, value in style.items():
            setattr(self, key, value)

        # コンテンツの設定
        self.content = ft.Column(
            controls=[self._create_content()],
            expand=True,
        )

        # イベントハンドラの設定
        if self._enable_hover:
            self.on_hover = self._on_hover
        if self._enable_press:
            self.on_click = self._on_click

    def update_options(self, new_options):
        """ドロップダウンの選択肢を更新"""
        self.options = new_options
        self._setup_container()
        self.update()

    def set_value(self, value):
        """値を設定"""
        self.value = value
        self._setup_container()
        self.update()

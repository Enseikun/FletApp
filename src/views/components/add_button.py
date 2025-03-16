"""
追加ボタンコンポーネント
アイコンボタンを使用して追加アクションを提供する
"""

import flet as ft

from src.views.styles.style import Colors


class AddButton(ft.IconButton):
    """
    追加アクションを提供するシンプルなアイコンボタン
    ft.IconButtonの基本機能のみを使用
    """

    def __init__(
        self,
        on_click=None,
        tooltip="追加",
        size=40,
        disabled=False,
        visible=True,
    ):
        # 基底クラスの初期化
        super().__init__(
            icon=ft.icons.ADD_CIRCLE,
            icon_color=Colors.PRIMARY,
            icon_size=size,
            tooltip=tooltip,
            on_click=on_click,
            disabled=disabled,
            visible=visible,
        )

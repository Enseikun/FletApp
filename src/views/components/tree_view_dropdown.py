"""
ツリービュードロップダウンコンポーネント
階層構造を持つデータを表示するためのカスタムドロップダウン
"""

from typing import Any, Dict, List, Optional, Union

import flet as ft

from src.views.components.mixins.event_handling_mixin import EventHandlingMixin
from src.views.components.mixins.state_management_mixin import StateManagementMixin
from src.views.components.mixins.ui_component_mixin import UIComponentMixin
from src.views.styles.style import ComponentState


class TreeViewDropdown(
    ft.Container, StateManagementMixin, UIComponentMixin, EventHandlingMixin
):
    """
    階層構造を持つデータを表示するためのカスタムドロップダウン
    フォルダ構造などの階層データを視覚的に表示する
    """

    def __init__(
        self,
        label: str,
        icon: ft.icons,
        on_change: Optional[callable] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        **kwargs,
    ):
        """
        初期化

        Args:
            label (str): ドロップダウンのラベル
            icon (ft.icons): 表示するアイコン
            on_change (Optional[callable]): 選択変更時のコールバック関数
            width (Optional[int]): コンポーネントの幅
            height (Optional[int]): コンポーネントの高さ
            **kwargs: その他のキーワード引数
        """
        super().__init__()

        # プロパティの設定
        self.label = label
        self.icon = icon
        self.on_change_callback = on_change
        self.width = width
        self.height = height or 300
        self.selected_value = None
        self.options = []
        self._is_dropdown_visible = False  # ドロップダウンの表示状態を管理

        # 状態管理の初期化
        self.init_state_management(**kwargs)

        # コンテナの設定
        self._setup_container()
        self.expand = True

    def _create_dropdown_button(self):
        """ドロップダウンボタンを作成"""
        style = self._get_current_style()

        return ft.ElevatedButton(
            text=self.label,
            icon=self.icon,
            on_click=self._toggle_dropdown,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=10,
            ),
            width=self.width,
            disabled=not self._enabled,
            color=style.text_color,
        )

    def _create_tree_view(self):
        """ツリービューを作成"""
        return ft.TreeView(
            expand=1,
            selectable=True,
            on_select=self._on_select,
        )

    def _create_dropdown_content(self):
        """ドロップダウンコンテンツを作成"""
        style = self._get_current_style()

        return ft.Container(
            content=self._create_tree_view(),
            visible=self._is_dropdown_visible,  # 表示状態を反映
            bgcolor=style.bgcolor,
            border=ft.border.all(1, style.border_color),
            border_radius=8,
            padding=10,
            max_height=self.height,
            scroll=ft.ScrollMode.AUTO,
            width=self.width,
        )

    def _create_content(self):
        """コンポーネントのコンテンツを作成"""
        return ft.Column(
            controls=[
                self._create_dropdown_button(),
                self._create_dropdown_content(),
            ],
            width=self.width,
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

    def _toggle_dropdown(self, e):
        """ドロップダウンの表示/非表示を切り替え"""
        if not self._enabled:
            return

        self._is_dropdown_visible = not self._is_dropdown_visible
        self._setup_container()  # コンテンツを再作成
        self.update()

    def _on_select(self, e):
        """フォルダ選択時の処理"""
        if not self._enabled:
            return

        self.selected_value = e.control.data
        dropdown_button = self.content.controls[0]
        dropdown_button.text = e.control.label
        dropdown_content = self.content.controls[1]
        dropdown_content.visible = False

        if self.on_change_callback:
            # イベントオブジェクトを作成して親コンポーネントに渡す
            e.control = self
            self.on_change_callback(e)

        self.update()

    def update_options(self, options: List[Dict[str, Any]]):
        """
        フォルダオプションを更新

        Args:
            options (List[Dict[str, Any]]): フォルダ情報のリスト
        """
        self.options = options
        tree_view = self.content.controls[1].content
        tree_view.controls.clear()
        self._add_folder_nodes(options)
        self.update()

    def _add_folder_nodes(
        self, folders: List[Dict[str, Any]], parent_id: str = None, level: int = 0
    ):
        """
        フォルダノードを再帰的に追加

        Args:
            folders (List[Dict[str, Any]]): フォルダ情報のリスト
            parent_id (str, optional): 親フォルダのID. Defaults to None.
            level (int, optional): 階層レベル. Defaults to 0.
        """
        style = self._get_current_style()

        for folder in folders:
            if folder.get("parent_folder_id") == parent_id:
                # 未読数がある場合は表示
                label = folder["name"]
                if "unread_count" in folder and folder["unread_count"] > 0:
                    label = f"{label} ({folder['unread_count']})"

                node = ft.TreeViewNode(
                    label=label,
                    data=folder["id"],
                    icon=ft.icons.FOLDER,
                    padding=ft.padding.only(left=level * 20),
                    color=style.text_color,
                )
                tree_view = self.content.controls[1].content
                tree_view.controls.append(node)
                self._add_folder_nodes(folders, folder["id"], level + 1)

    def get_value(self) -> str:
        """
        選択された値を取得

        Returns:
            str: 選択された値
        """
        return self.selected_value

    def set_value(self, value: str):
        """
        値を設定

        Args:
            value (str): 設定する値
        """
        self.selected_value = value
        self.update()

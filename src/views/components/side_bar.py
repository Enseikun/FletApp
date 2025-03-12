"""
アプリケーションのサイドバーコンポーネント
NavigationRailを使用したサイドナビゲーション
"""

import flet as ft


class SideBar(ft.NavigationRail):
    """
    アプリケーションのサイドバーコンポーネント
    """

    def __init__(self, viewmodel=None):
        """
        初期化

        Args:
            viewmodel (SideBarViewModel, optional): サイドバーのビューモデル
        """
        self.viewmodel = viewmodel

        # デスティネーションの定義
        destinations = [
            ft.NavigationRailDestination(
                icon=ft.icons.HOME_OUTLINED,
                selected_icon=ft.icons.HOME,
                label="ホーム",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.MENU_BOOK_OUTLINED,
                selected_icon=ft.icons.MENU_BOOK,
                label="プレビュー",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.SETTINGS_OUTLINED,
                selected_icon=ft.icons.SETTINGS,
                label="設定",
            ),
        ]

        # デスティネーションキーのマッピング
        self.destination_keys = ["home", "preview", "settings"]

        super().__init__(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            extended=True,
            min_width=100,
            min_extended_width=200,
            destinations=destinations,
            on_change=self._on_change_internal,
        )

    def _on_change_internal(self, e):
        """
        内部のon_changeイベントハンドラ
        選択されたインデックスからデスティネーションキーを取得してビューモデルに通知
        """
        if self.viewmodel:
            selected_key = self.destination_keys[e.control.selected_index]
            self.viewmodel.select_destination(selected_key)

    def update_selected_destination(self, destination_key):
        """
        選択されたデスティネーションを更新

        Args:
            destination_key (str): 選択するデスティネーションキー
        """
        if destination_key in self.destination_keys:
            index = self.destination_keys.index(destination_key)
            if self.selected_index != index:
                self.selected_index = index
                self.update()

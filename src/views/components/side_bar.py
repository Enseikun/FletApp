"""
アプリケーションのサイドバーコンポーネント
NavigationRailを使用したサイドナビゲーション
"""

import flet as ft


class SideBar(ft.NavigationRail):
    """
    アプリケーションのサイドバーコンポーネント
    """

    def __init__(self):
        super().__init__(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.icons.HOME_OUTLINED,
                    selected_icon=ft.icons.HOME,
                    label="ホーム",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.SETTINGS_OUTLINED,
                    selected_icon=ft.icons.SETTINGS,
                    label="設定",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.PERSON_OUTLINED,
                    selected_icon=ft.icons.PERSON,
                    label="プロフィール",
                ),
            ],
            on_change=self._handle_on_change,
        )

        # Destinationが変更されたときのコールバック
        self.on_destination_change = None

        # Destinationのキーマッピング
        self.destination_keys = ["home", "settings", "profile"]

    def _handle_on_change(self, e):
        """
        NavigationRailの選択変更イベントを処理する

        Args:
            e: イベントデータ
        """
        if self.on_destination_change is not None:
            # 選択されたインデックスに対応するキーを取得
            selected_key = self.destination_keys[self.selected_index]
            # コールバックを呼び出す
            self.on_destination_change(selected_key)

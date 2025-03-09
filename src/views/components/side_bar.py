import flet as ft

from src.viewmodels.side_bar_viewmodel import SideBarViewModel


class SideBar(ft.NavigationBar):
    def __init__(self):
        super().__init__()

        # Destination変更時のコールバック
        self.on_destination_change = None

        self.destinations = [
            ft.NavigationDestination(
                icon=ft.icons.HOME_OUTLINED,
                selected_icon=ft.icons.HOME,
                label="ホーム",
            ),
            ft.NavigationDestination(
                icon=ft.icons.SETTINGS_OUTLINED,
                selected_icon=ft.icons.SETTINGS,
                label="設定",
            ),
            ft.NavigationDestination(
                icon=ft.icons.PERSON_OUTLINED,
                selected_icon=ft.icons.PERSON,
                label="プロフィール",
            ),
        ]

        # Destinationのキーマッピング
        self.destination_keys = ["home", "settings", "profile"]

        # イベントハンドラを設定
        self.on_change = self.handle_change

    def handle_change(self, e):
        """NavigationBarの選択変更イベントを処理"""
        selected_index = e.control.selected_index

        # インデックスが有効範囲内かチェック
        if 0 <= selected_index < len(self.destination_keys):
            destination_key = self.destination_keys[selected_index]

            # コールバックが設定されていれば呼び出す
            if self.on_destination_change:
                self.on_destination_change(destination_key)

import flet as ft

from src.viewmodels.side_bar_viewmodel import SideBarViewModel


class SideBar(ft.NavigationRail):
    def __init__(self, viewmodel: SideBarViewModel):
        super().__init__()
        self.viewmodel = viewmodel
        self.selected_index = self.viewmodel.selected_index

        # ビューモデルの状態変更を監視
        self.viewmodel.add_listener(self._on_index_change)

        # NavigationRailの設定
        self.label_type = ft.NavigationRailLabelType.ALL
        self.min_width = 100
        self.min_extended_width = 150
        self.destinations = [
            ft.NavigationRailDestination(
                icon=ft.icons.HOME_OUTLINED, selected_icon=ft.icons.HOME, label="HOME"
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.PREVIEW_OUTLINED,
                selected_icon=ft.icons.PREVIEW,
                label="PREVIEW",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.SETTINGS_OUTLINED,
                selected_icon=ft.icons.SETTINGS,
                label="SETTING",
            ),
        ]

        self.on_change = self._handle_destination_change

    def _handle_destination_change(self, e):
        self.viewmodel.selected_index = e.control.selected_index

    def _on_index_change(self, index: int):
        self.selected_index = index
        self.update()

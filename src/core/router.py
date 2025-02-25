from typing import Dict, Type

import flet as ft

from views.first_view import FirstView
from views.interfaces.view_interface import ViewInterface
from views.second_view import SecondView


class Router:
    def __init__(self, page: ft.Page):
        self.page = page
        self.shared_data: dict = {}
        self.views: Dict[str, ViewInterface] = {
            "/": FirstView(page),
            "/second": SecondView(page),
        }

        # ルート設定
        self.page.on_route_change = self._on_route_change
        self.page.views.clear()
        self.views["/"].display()

    def _on_route_change(self, route):
        new_route = route.route
        if new_route in self.views:
            view = self.views[new_route]
            view.display()
            view.update_with_shared_data(self.shared_data)

    def update_shared_data(self, data: dict):
        self.shared_data.update(data)
        # 必要に応じて特定のビューを更新
        for view in self.page.views:
            if hasattr(view, "update_with_shared_data"):
                view.update_with_shared_data(self.shared_data)

    def navigate(self, route: str, data: dict = None):
        """指定されたルートに遷移し、必要に応じてデータを更新する"""
        if data:
            self.update_shared_data(data)
        self.page.go(route)
        return self.views[route]

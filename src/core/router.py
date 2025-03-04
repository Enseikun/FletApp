from dataclasses import dataclass
from typing import Dict, Optional, Type

from flet import Control, Page, View


@dataclass
class RouteConfig:
    view_class: Type[View]
    title: str
    params: dict = None


# # ルーターでの使用例
# router = Router(page)
# router.add_route(
#     path="/products/1",
#     view_class=ProductDetailView,
#     title="商品詳細",
#     params={
#         "product_id": 1,
#         "initial_tab": "reviews"
#     }
# )


class Router:
    def __init__(self, page: Page):
        self.page = page
        self.routes: Dict[str, RouteConfig] = {}
        self.current_route: Optional[str] = None
        self.history: list[str] = []

    def add_route(
        self, path: str, view_class: Type[View], title: str, params: dict = None
    ):
        """
        新しいルートを追加します

        Args:
            path: ルートのパス（例: "/home"）
            view_class: ビューのクラス
            title: ページのタイトル
            params: ビューに渡す追加パラメータ
        """
        self.routes[path] = RouteConfig(
            view_class=view_class, title=title, params=params or {}
        )

    def navigate(self, path: str):
        """
        指定されたパスに遷移します

        Args:
            path: 遷移先のパス
        """
        if path not in self.routes:
            raise ValueError(f"Route not found: {path}")

        route_config = self.routes[path]

        # 新しいビューを作成
        view = route_config.view_class(route=path, **route_config.params)

        # ページの更新
        self.page.title = route_config.title
        self.page.views.clear()
        self.page.views.append(view)

        # 履歴の更新
        self.current_route = path
        self.history.append(path)

        self.page.update()

    def back(self) -> bool:
        """
        前のページに戻ります

        Returns:
            bool: 戻ることができた場合はTrue
        """
        if len(self.history) <= 1:
            return False

        self.history.pop()  # 現在のルートを削除
        previous_route = self.history[-1]  # 前のルートを取得

        # 前のルートに遷移
        route_config = self.routes[previous_route]
        view = route_config.view_class(route=previous_route, **route_config.params)

        self.page.title = route_config.title
        self.page.views.clear()
        self.page.views.append(view)
        self.current_route = previous_route

        self.page.update()
        return True

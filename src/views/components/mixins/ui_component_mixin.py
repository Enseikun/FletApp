"""
UIコンポーネントの基本機能を提供するミックスイン
"""

from typing import Any

import flet as ft


class UIComponentMixin:
    """UIコンポーネントの基本機能を提供するミックスイン"""

    def _create_content(self) -> Any:
        raise NotImplementedError(
            "サブクラスで_create_contentをオーバーライドしてください"
        )

    def _create_container(self) -> ft.Container:
        style = self._get_current_style().to_dict()
        handlers = self._get_event_handlers()

        return ft.Container(
            content=self._create_content(),
            **handlers,
            **style,
        )

    def build(self):
        return self._create_container()

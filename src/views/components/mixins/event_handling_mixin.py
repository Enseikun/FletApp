"""
イベント処理機能を提供するミックスイン
"""

from typing import Protocol

from src.views.styles.style import ComponentState, ComponentStyle


class StateManagementProtocol(Protocol):
    """状態管理機能のプロトコル"""

    _enabled: bool
    _enable_hover: bool
    _enable_press: bool
    _state: ComponentState
    _styles: dict

    def _setup_container(self) -> None: ...
    def update(self) -> None: ...
    def _get_current_style(self) -> "ComponentStyle": ...


class EventHandlingMixin:
    """
    イベント処理機能を提供するミックスイン
    StateManagementMixinと組み合わせて使用することを前提としています
    """

    def _get_event_handlers(self):
        handlers = {}
        if self._enable_hover:
            handlers["on_hover"] = self._on_hover
        if self._enable_press:
            handlers["on_click"] = self._on_click
        return handlers

    def _on_hover(self, e):
        """ホバーイベントのハンドラ"""
        if not self._enabled or not self._enable_hover:
            return

        # アクティブ状態の場合はホバー効果を適用しない
        if self._state == ComponentState.ACTIVE:
            return

        new_state = (
            ComponentState.HOVERED if e.data == "true" else ComponentState.NORMAL
        )
        try:
            self.set_state(new_state)
        except AttributeError:
            pass  # 描画されていない場合は無視

    def _on_click(self, e):
        """クリックイベントのハンドラ"""
        if not self._enabled or not self._enable_press:
            return

        # プレス状態に設定
        self.set_state(ComponentState.PRESSED)

        # コールバックが設定されている場合は呼び出す
        if self.on_click_callback and self._enabled:
            # 自分自身をコントロールとして渡す
            e.control = self
            self.on_click_callback(e)

        # クリック後に通常状態に戻す
        if self._enabled:
            new_state = (
                ComponentState.NORMAL
                if self._state != ComponentState.ACTIVE
                else ComponentState.ACTIVE
            )
            self.set_state(new_state)

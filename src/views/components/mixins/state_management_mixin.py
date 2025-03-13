"""
状態管理機能を提供するミックスイン
"""

from typing import Callable, Dict, Optional

from src.views.styles.style import ComponentState, ComponentStyle, StyleManager

# 状態の優先順位を定義
# 数値が小さいほど優先度が高い
PRIORITY: Dict[ComponentState, int] = {
    ComponentState.DISABLED: 0,  # 無効状態は最優先（他の状態に遷移させない）
    ComponentState.ERROR: 1,  # エラー状態は次に優先
    ComponentState.ACTIVE: 2,  # アクティブ状態は通常のインタラクションより優先
    ComponentState.PRESSED: 3,  # プレス状態は一時的
    ComponentState.HOVERED: 4,  # ホバー状態は最も優先度が低い
    ComponentState.NORMAL: 5,  # 通常状態はデフォルト
}


class StateManagementMixin:
    """状態管理機能を提供するミックスイン"""

    def init_state_management(
        self,
        enabled: bool = True,
        enable_hover: bool = True,
        enable_press: bool = True,
        activate: bool = False,
        on_click_callback: Optional[Callable] = None,
    ):
        self._enabled = enabled
        self._enable_hover = enable_hover
        self._enable_press = enable_press
        self.on_click_callback = on_click_callback
        self._styles = StyleManager.get_default_styles()
        self._setup_initial_state(enabled, activate)

    def _setup_initial_state(self, enabled: bool, activate: bool):
        if not enabled:
            self._state = ComponentState.DISABLED
        elif activate:
            self._state = ComponentState.ACTIVE
        else:
            self._state = ComponentState.NORMAL

    def _get_current_style(self):
        return self._styles[self._state]

    def enable(self):
        """コンポーネントを有効化"""
        self._enabled = True
        self._state = ComponentState.NORMAL
        self._setup_container()
        self.update()

    def disable(self):
        """コンポーネントを無効化"""
        self._enabled = False
        self._state = ComponentState.DISABLED
        self._setup_container()
        self.update()

    def activate(self):
        """コンポーネントをアクティブ状態に設定"""
        if not self._enabled:
            return
        self._state = ComponentState.ACTIVE
        self._setup_container()
        self.update()

    def deactivate(self):
        """コンポーネントを非アクティブ状態に設定"""
        if not self._enabled:
            return
        self._state = ComponentState.NORMAL
        self._setup_container()
        self.update()

    def set_error(self, has_error: bool = True):
        """エラー状態を設定"""
        if not self._enabled:
            return

        if has_error:
            self._state = ComponentState.ERROR
        else:
            self._state = ComponentState.NORMAL
        self._setup_container()
        self.update()

    def set_state(self, state: ComponentState):
        """コンポーネントの状態を直接設定"""
        if not self._enabled:
            return

        current_priority = PRIORITY[self._state]
        new_priority = PRIORITY[state]

        # 優先度の高い状態は維持
        if current_priority <= new_priority and state != ComponentState.NORMAL:
            return

        self._state = state
        self._setup_container()
        self.update()

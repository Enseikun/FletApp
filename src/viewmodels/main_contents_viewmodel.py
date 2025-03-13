from typing import Optional

from src.views.styles.style import ComponentState


class MainContentsViewModel:
    def __init__(self):
        self._last_pressed_component_id: Optional[str] = None
        self._observers = []

    @property
    def last_pressed_component_id(self) -> Optional[str]:
        return self._last_pressed_component_id

    def set_last_pressed_component(self, component_id: str) -> None:
        # 前回選択されていたコンポーネントの状態をリセット
        if self._last_pressed_component_id:
            self._notify_observers(
                ComponentState.NORMAL, self._last_pressed_component_id
            )

        # 新しいコンポーネントを記録
        self._last_pressed_component_id = component_id
        self._notify_observers(ComponentState.ACTIVE, component_id)

    def add_observer(self, observer):
        self._observers.append(observer)

    def _notify_observers(self, state: ComponentState, component_id: str):
        for observer in self._observers:
            observer.on_component_state_changed(state, component_id)

from typing import Callable


class SideBarViewModel:
    def __init__(self):
        self._selected_index: int = 0
        self._on_change_callbacks: list[Callable[[int], None]] = []

    @property
    def selected_index(self) -> int:
        return self._selected_index

    @selected_index.setter
    def selected_index(self, value: int) -> None:
        self._selected_index = value
        self._notify_listeners()

    def add_listener(self, callback: Callable[[int], None]) -> None:
        self._on_change_callbacks.append(callback)

    def _notify_listeners(self) -> None:
        for callback in self._on_change_callbacks:
            callback(self._selected_index)

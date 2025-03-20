import asyncio
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union

T = TypeVar("T")


class Observable:
    def __init__(self):
        # イベント名をキーとし、オブザーバー関数のセットを値とする辞書
        self._observers: Dict[str, Set[Callable[[Optional[Any]], Any]]] = {}
        # グローバルオブザーバー（すべてのイベントで呼び出される）のセット
        self._global_observers: Set[Callable[[str, Optional[Any]], Any]] = set()

    def add_observer(
        self, observer: Callable[[Optional[Any]], Any], event: str = "default"
    ) -> None:
        """特定のイベントに対するオブザーバーを追加します"""
        if event not in self._observers:
            self._observers[event] = set()
        self._observers[event].add(observer)

    def remove_observer(
        self, observer: Callable[[Optional[Any]], Any], event: str = "default"
    ) -> None:
        """特定のイベントからオブザーバーを削除します"""
        if event in self._observers and observer in self._observers[event]:
            self._observers[event].remove(observer)

    def add_global_observer(
        self, observer: Callable[[str, Optional[Any]], Any]
    ) -> None:
        """すべてのイベントで呼び出されるグローバルオブザーバーを追加します"""
        self._global_observers.add(observer)

    def remove_global_observer(
        self, observer: Callable[[str, Optional[Any]], Any]
    ) -> None:
        """グローバルオブザーバーを削除します"""
        if observer in self._global_observers:
            self._global_observers.remove(observer)

    async def notify_observers(self, event: str = "default", data: Any = None) -> None:
        """特定のイベントに登録されたオブザーバーに通知します"""
        tasks = []

        # イベント固有のオブザーバーを呼び出し
        if event in self._observers:
            for observer in list(self._observers[event]):
                try:
                    if asyncio.iscoroutinefunction(observer):
                        tasks.append(observer(data))
                    else:
                        observer(data)
                except Exception as e:
                    print(f"Observer error: {e}")

        # 非同期タスクを並列実行
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def notify_global_observers(
        self, event: str = "default", data: Any = None
    ) -> None:
        """すべてのグローバルオブザーバーに通知します"""
        tasks = []

        for observer in list(self._global_observers):
            try:
                if asyncio.iscoroutinefunction(observer):
                    tasks.append(observer(event, data))
                else:
                    observer(event, data)
            except Exception as e:
                print(f"Global observer error: {e}")

        # 非同期タスクを並列実行
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def notify_all(self, event: str = "default", data: Any = None) -> None:
        """イベント固有のオブザーバーとグローバルオブザーバーの両方に通知します"""
        await self.notify_observers(event, data)
        await self.notify_global_observers(event, data)

    def clear_observers(self) -> None:
        """すべてのオブザーバーをクリアします"""
        self._observers.clear()
        self._global_observers.clear()

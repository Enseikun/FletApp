from abc import ABC, abstractmethod
from typing import Any, Optional


class ModelInterface(ABC):
    @abstractmethod
    async def fetch_data(self) -> Any:
        """データの取得"""
        pass

    @abstractmethod
    async def save_data(self, data: Any) -> bool:
        """データの保存"""
        pass

    @abstractmethod
    async def update_data(self, id: str, data: Any) -> Optional[Any]:
        """データの更新"""
        pass

    @abstractmethod
    async def delete_data(self, id: str) -> bool:
        """データの削除"""
        pass

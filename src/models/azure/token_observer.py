import asyncio
from asyncio import Lock  # 非同期
from collections import deque
from datetime import datetime

# from threading import Lock # 同期
from typing import Deque, Final, Optional, Protocol, Set, Tuple

from src.core.logger import get_logger
from src.models.azure.ai_config_loader import AIConfigLoader


# Observer Protocol
class TokenObserver(Protocol):
    """トークンの完了と追加を通知"""

    async def on_token_completed(self, token_count: int) -> None:
        """トークンが完了したときに呼び出される"""
        ...

    async def on_token_added(self, token_count: int) -> None:
        """トークンが追加されたときに呼び出される"""
        ...


class TokenSubject:
    """オブザーバーの管理と通知"""

    def __init__(self) -> None:
        self._observers: Set[TokenObserver] = set()
        self._lock = Lock()
        self.logger = get_logger()

    def attach(self, observer: TokenObserver) -> None:
        self._observers.add(observer)

    def detach(self, observer: TokenObserver) -> None:
        self._observers.remove(observer)

    async def notify_token_completed(self, token_count: int) -> None:
        for observer in self._observers:
            try:
                await observer.on_token_completed(token_count)
            except Exception as e:
                self.logger.error(f"エラーが発生しました: {e}")

    async def notify_token_added(self, token_count: int) -> None:
        for observer in self._observers:
            try:
                await observer.on_token_added(token_count)
            except Exception as e:
                self.logger.error(f"エラーが発生しました: {e}")


class TokenRateLimiter(TokenObserver):
    """トークンの状態変更を監視（TokenObserverとして実装）"""

    def __init__(self, max_tpm: int) -> None:
        config = AIConfigLoader()
        self.max_tpm = max_tpm
        self.window_size = 60
        self.token_history: Deque[Tuple[datetime, int]] = deque()
        self.lock = Lock()
        self.active_tokens = 0
        self.waiting_tokens: Deque[Tuple[int, asyncio.Event, datetime]] = deque()
        self.timeout = config.token_timeout  # 設定ファイルから取得
        self.cleanup_threshold = 100
        self.logger = get_logger()

    async def on_token_completed(self, token_count: int) -> None:
        async with self.lock:
            self.active_tokens -= token_count
            await self._process_waiting_tokens()

    async def on_token_added(self, token_count: int) -> None:
        async with self.lock:
            self.active_tokens += token_count
            current_time = datetime.now()
            self.token_history.append((current_time, token_count))
            self._cleanup_history(current_time)

    async def _process_waiting_tokens(self) -> None:
        while self.waiting_tokens:
            token_count, event, timestamp = self.waiting_tokens[0]
            if await self._can_process_tokens(token_count):
                self.waiting_tokens.popleft()
                self.active_tokens += token_count
                event.set()
            else:
                break

    async def can_process_tokens(self, token_count: int) -> bool:
        current_tpm = await self.get_current_tpm()
        return current_tpm + token_count <= self.max_tpm

    async def get_current_tpm(self) -> int:
        current_time = datetime.now()
        async with self.lock:
            self._cleanup_history(current_time)
            return sum(tokens for _, tokens in self.token_history)

    def _cleanup_history(self, current_time: datetime) -> None:
        while (
            self.token_history
            and (current_time - self.token_history[0][0]).total_seconds()
            >= self.window_size
        ):
            self.token_history.popleft()

    async def _cleanup_waiting_tokens(self) -> None:
        current_time = datetime.now()
        async with self.lock:
            self.waiting_tokens = deque(
                (token_count, event, timestamp)
                for token_count, event, timestamp in self.waiting_tokens
                if (current_time - timestamp).total_seconds() < self.timeout
            )

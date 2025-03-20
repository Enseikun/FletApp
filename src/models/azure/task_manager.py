import asyncio
from datetime import datetime
from typing import Callable, Dict, List, Optional

from src.core.logger import get_logger
from src.models.azure.openai_client import OpenAIClient
from src.models.azure.token_observer import (
    TokenObserver,
    TokenRateLimiter,
    TokenSubject,
)


class TaskManager:
    def __init__(self, openai_client: OpenAIClient):
        self.openai_client = openai_client
        self.token_subject = TokenSubject()
        self.token_rate_limiter = TokenRateLimiter()
        self.token_subject.attach(self.token_rate_limiter)
        self.token_subject.attach(self.LoggingObserver())
        self.tasks = []
        self.logger = get_logger()

    class LoggingObserver(TokenObserver):
        def __init__(self):
            self.logger = get_logger()

        async def on_token_completed(self, token_count: int) -> None:
            self.logger.info(f"Token completed: {token_count}")

        async def on_token_added(self, token_count: int) -> None:
            self.logger.info(f"Token added: {token_count}")

    async def execute_tasks(
        self, prompts: List[str], callback: Callable[[str, Optional[str]], None]
    ) -> List[str]:
        """複数プロンプトを非同期タスクとして実行"""
        if not prompts:
            raise ValueError("プロンプトが空です")

        if not callable(callback):
            raise ValueError("コールバックが関数ではありません")

        async def task_wrapper(prompt: str) -> None:
            try:
                result = await asyncio.wait_for(self.send_prompt(prompt), timeout=30)
                await callback(prompt, result)
            except asyncio.CancelledError:
                self.logger.warning(f"タスクがキャンセルされました: {prompt}")
            except TimeoutError:
                self.logger.warning(f"タスクがタイムアウトしました: {prompt}")
                await callback(prompt, None)
            except Exception as e:
                self.logger.error(f"タスクでエラーが発生しました: {prompt}, {e}")
                await callback(prompt, None)

        self.tasks = [asyncio.create_task(task_wrapper(prompt)) for prompt in prompts]

        try:
            await asyncio.gather(*self.tasks)
        except Exception as e:
            self.logger.error(f"タスクの実行中にエラーが発生しました: {e}")
            raise RuntimeError("タスクの実行中にエラーが発生しました")

    async def cancel_tasks(self) -> None:
        for task in self.tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except asyncio.CancelledError:
                    pass

        await asyncio.gather(
            *self.tasks, return_exceptions=True
        )  # キャンセル処理を待つ

    async def send_prompt(self, prompt: str) -> str:
        if not prompt:
            raise ValueError("プロンプトが空です")

        estimated_tokens = 0
        try:
            estimated_tokens = self.openai_client.estimate_tokens(prompt)
            self.logger.info(f"推定トークン数: {estimated_tokens}")

            # トークン量の管理
            await self.token_rate_limiter.add_tokens(estimated_tokens)
            await self.token_subject.notify_token_added(estimated_tokens)

            result = await self.openai_client.execute_prompt(prompt)

            if result is None:
                raise ValueError("レスポンスが空です")

            return result
        except Exception as e:
            self.logger.error(
                f"プロンプトの実行中にエラーが発生しました: {prompt}, {e}"
            )
            raise RuntimeError(
                f"プロンプトの実行中にエラーが発生しました: {prompt}, {e}"
            )
        finally:
            try:
                if estimated_tokens > 0:
                    await self.token_subject.notify_token_completed(estimated_tokens)
            except Exception as e:
                self.logger.error(f"トークン通知中にエラーが発生しました: {e}")
                # finallyブロック内で例外を発生させると元の例外が隠れてしまうためログ記録のみ

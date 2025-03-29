import asyncio
import json
from pathlib import Path
from typing import Dict, List, Union

from src.core.logger import get_logger
from src.models.azure.openai_client import OpenAIClient
from src.models.azure.task_manager import TaskManager


class AIReview:
    def __init__(self):
        self._logger = get_logger()
        self._lock = asyncio.Lock()
        self.client = None
        self.manager = None

    def _load_system_prompt(self, path: Path) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()  # 前後の空白を削除
        except FileNotFoundError:
            raise FileNotFoundError("prompt.txt not found")
        except Exception as e:
            raise Exception(f"Failed to load system prompt: {e}")

    def _create_threads(self):
        """AI入力用のJSONファイルを作成"""
        return [  # 仮の戻り値
            {"thread_id": "1", "content": "test1"},
            {"thread_id": "2", "content": "test2"},
        ]

    async def review(self):
        """AIレビュー"""
        self._create_threads()
        self.system_prompt = self._load_system_prompt("config/prompt.txt")
        self.threads = self._create_threads()

        # 実行
        self.client = OpenAIClient(system_prompt=self.system_prompt)
        self.manager = TaskManager(self.client)
        prompts = []

        for thread in self.threads:
            prompts.append(json.dumps(thread))

        async def callback(prompt: str, result: str):
            """AIレビューのコールバック関数"""
            async with self._lock:
                try:
                    if result is None:
                        self._logger.warning("AIレビュー結果がNoneです")
                        return

                    result_dict = json.loads(result)
                    user_prompt = json.loads(prompt)

                    # DBへの書き込み
                except Exception as e:
                    self._logger.error(f"コールバック処理でエラーが発生しました: {e}")
                    result_dict = {}

        # 実行
        await self.manager.execute_tasks(prompts, callback)

        # save

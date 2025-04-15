import asyncio
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypedDict, Union

from src.core.logger import get_logger
from src.models.azure.ai_config_loader import AIConfigLoader, ModelConfig
from src.models.azure.model_manager import ModelConfigDict, ModelManager
from src.models.azure.openai_client import OpenAIClient
from src.models.azure.task_manager import TaskManager, TaskManagerConfig


class ThreadData(TypedDict):
    thread_id: str
    content: str


class AIReviewResult(TypedDict, total=False):
    success: bool
    thread_id: str
    result: Optional[Dict[str, Any]]
    error: Optional[str]


class AIReview:
    def __init__(self):
        self._logger = get_logger()
        self._lock = asyncio.Lock()
        self.clients: Dict[str, OpenAIClient] = {}
        self.manager: Optional[TaskManager] = None
        self.system_prompt: str = ""
        self.threads: List[ThreadData] = []

    def _load_system_prompt(self, path: Path) -> str:
        """システムプロンプトを読み込む"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()  # 前後の空白を削除
        except FileNotFoundError:
            self._logger.error(f"プロンプトファイルが見つかりません: {path}")
            raise FileNotFoundError(f"プロンプトファイルが見つかりません: {path}")
        except Exception as e:
            self._logger.error(f"システムプロンプトの読み込みに失敗しました: {e}")
            raise Exception(f"システムプロンプトの読み込みに失敗しました: {e}")

    def _create_threads(self) -> List[ThreadData]:
        """AI入力用のスレッドデータを作成"""
        return [  # 仮の戻り値
            {"thread_id": "1", "content": "test1"},
            {"thread_id": "2", "content": "test2"},
        ]

    def _initialize_clients(self) -> None:
        """AIクライアントを初期化"""
        try:
            config = AIConfigLoader()
            if not config.models:
                raise ValueError("AIモデルの設定が見つかりません")

            # 各モデルのクライアントを初期化
            for model in config.models:
                self.clients[model.model_id] = OpenAIClient(
                    system_prompt=self.system_prompt, model_id=model.model_id
                )

            # モデルマネージャを初期化
            model_configs: Dict[str, ModelConfigDict] = {
                model.model_id: {
                    "rate_limits_tpm": model.rate_limits_tpm,
                    "rate_limits_rpm": model.rate_limits_rpm,
                }
                for model in config.models
            }

            model_manager = ModelManager(model_configs)

            # タスクマネージャを初期化
            task_config: TaskManagerConfig = {
                "mode": "loadbalance",
                "timeout": 30,
                "retry_count": 2,
            }
            self.manager = TaskManager(self.clients, model_manager, task_config)

        except Exception as e:
            self._logger.error(f"AIクライアントの初期化に失敗しました: {e}")
            raise RuntimeError(f"AIクライアントの初期化に失敗しました: {e}")

    async def review(self) -> List[AIReviewResult]:
        """AIレビューを実行"""
        results: List[AIReviewResult] = []

        try:
            # スレッドデータを準備
            self.threads = self._create_threads()
            if not self.threads:
                self._logger.warning("レビュー対象のスレッドがありません")
                return results

            # システムプロンプトを読み込み
            self.system_prompt = self._load_system_prompt(Path("config/prompt.txt"))

            # クライアントを初期化
            self._initialize_clients()

            if not self.manager:
                raise RuntimeError("タスクマネージャが初期化されていません")

            # リクエスト用プロンプトを準備
            prompts: List[str] = []
            thread_map: Dict[str, ThreadData] = {}

            for thread in self.threads:
                thread_json = json.dumps(thread)
                prompts.append(thread_json)
                # プロンプトの内容からスレッドを逆引きするためのマップ
                thread_map[thread_json] = thread

            # コールバック関数を定義
            async def callback(prompt: str, result: Optional[str]) -> None:
                """AIレビューのコールバック関数"""
                async with self._lock:
                    review_result: AIReviewResult = {"success": False}

                    try:
                        thread = thread_map.get(prompt)
                        if not thread:
                            self._logger.warning(f"未知のプロンプト: {prompt[:50]}...")
                            return

                        review_result["thread_id"] = thread["thread_id"]

                        if result is None:
                            self._logger.warning(
                                f"スレッド {thread['thread_id']} のAIレビュー結果がNoneです"
                            )
                            review_result["error"] = "AIレビュー結果がありません"
                            results.append(review_result)
                            return

                        # 結果をパース
                        result_dict = json.loads(result)
                        review_result["success"] = True
                        review_result["result"] = result_dict
                        results.append(review_result)

                        # DBへの書き込みなどの処理...

                    except json.JSONDecodeError as e:
                        self._logger.error(
                            f"APIレスポンスのJSONパースに失敗しました: {e}"
                        )
                        review_result["error"] = f"レスポンスのパースに失敗: {str(e)}"
                        results.append(review_result)
                    except Exception as e:
                        self._logger.error(
                            f"コールバック処理でエラーが発生しました: {e}"
                        )
                        review_result["error"] = f"処理エラー: {str(e)}"
                        results.append(review_result)

            # タスクを実行
            await self.manager.execute_tasks(prompts, callback)

            return results

        except Exception as e:
            self._logger.error(f"AIレビュー実行中にエラーが発生しました: {e}")
            raise RuntimeError(f"AIレビュー実行中にエラーが発生しました: {e}")

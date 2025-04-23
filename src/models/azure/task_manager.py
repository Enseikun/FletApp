import asyncio
import time
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional, Tuple, TypedDict

from src.core.logger import get_logger
from src.models.azure.model_manager import ModelManager, ModelMetrics
from src.models.azure.openai_client import OpenAIClient
from src.models.azure.token_observer import TokenObserver
from src.util.visualize_model_status import print_model_statuses_async


class TaskManagerConfig(TypedDict, total=False):
    mode: str
    timeout: int
    retry_count: int


class TaskManager:
    def __init__(
        self,
        openai_client: Dict[str, OpenAIClient],
        model_manager: ModelManager,
        config: Optional[TaskManagerConfig] = None,
    ):
        self.openai_client = openai_client
        self.model_manager = model_manager
        self.config = config or {"mode": "priority", "timeout": 30, "retry_count": 1}
        self.mode = self.config.get("mode", "priority")
        self.timeout = self.config.get("timeout", 30)
        self.retry_count = self.config.get("retry_count", 1)
        self.tasks = []
        self.logger = get_logger()

    async def execute_tasks(
        self, prompts: List[str], callback: Callable[[str, Optional[str]], None]
    ) -> None:
        if not prompts:
            raise ValueError("プロンプトが空です")

        if not callable(callback):
            raise ValueError("コールバックが関数ではありません")

        async def task_wrapper(prompt: str) -> None:
            model_id, result, token_cost, latency = await self.process_prompt(prompt)
            await callback(prompt, result)
            await print_model_statuses_async(self.model_manager)

            if model_id:
                metrics = self.model_manager.get_model_metrics(model_id)
                if metrics:
                    try:
                        await metrics.complete_request(latency, token_cost)
                    except Exception as e:
                        self.logger.error(
                            f"モデルメトリクスの更新中にエラーが発生しました: {e}"
                        )

        self.tasks = [asyncio.create_task(task_wrapper(prompt)) for prompt in prompts]

        try:
            await asyncio.gather(*self.tasks)
        except asyncio.TimeoutError:
            self.logger.error("タスクの実行がタイムアウトしました")
            await self.cancel_tasks()
        except asyncio.CancelledError:
            self.logger.warning("タスクの実行がキャンセルされました")
            await self.cancel_tasks()
        except Exception as e:
            self.logger.error(f"タスクの実行中にエラーが発生しました: {e}")
            await self.cancel_tasks()
            raise RuntimeError(f"タスクの実行中にエラーが発生しました: {e}")

    async def process_prompt(
        self, prompt: str
    ) -> Tuple[Optional[str], Optional[str], int, float]:
        """
        プロンプトを処理し、モデルID、結果、トークンコスト、レスポンス時間を返す
        """
        candidate_model_id = None
        selected_client = None
        token_cost = 0
        attempts = 0

        while attempts < self.retry_count:
            try:
                # 優先モードの場合は設定ファイルの順番に従って候補を抽出
                if self.mode == "priority":
                    for model_id in self.openai_client.keys():
                        client = self.openai_client[model_id]
                        token_cost = self._estimate_token_cost(client, prompt)
                        metrics = self.model_manager.get_model_metrics(model_id)
                        if metrics and await metrics.can_accept_request(token_cost):
                            candidate_model_id = model_id
                            selected_client = client
                            break

                # 負荷分散モードの場合は全体からスコア（レイテンシとトークン余裕度の組み合わせ）が最適なモデルを選択
                elif self.mode == "loadbalance":
                    best_score = float("-inf")
                    for model_id, client in self.openai_client.items():
                        token_cost = self._estimate_token_cost(client, prompt)
                        metrics = self.model_manager.get_model_metrics(model_id)
                        if metrics and await metrics.can_accept_request(token_cost):
                            # トークン余裕度を取得 (0.0 ~ 1.0)
                            token_availability = await metrics.get_token_availability()

                            # 平均レイテンシを取得し、正規化 (低いほど良い)
                            avg_latency = metrics.get_average_latency()
                            # 初回リクエストの場合は仮の値を設定
                            if avg_latency == 0.0:
                                avg_latency = 0.1

                            # スコアの計算: トークン余裕度(高いほど良い) - 正規化レイテンシ(低いほど良い)
                            # レイテンシは秒単位で通常0.1~10程度なので、適切な重みをつける
                            latency_factor = min(
                                1.0, avg_latency / 10.0
                            )  # 10秒以上は1.0に正規化

                            # 最終スコア: トークン余裕度の重み0.7、レイテンシの重み0.3
                            score = (0.7 * token_availability) - (0.3 * latency_factor)

                            self.logger.debug(
                                f"モデル: {model_id}, トークン余裕度: {token_availability:.2f}, "
                                f"レイテンシ: {avg_latency:.2f}秒, スコア: {score:.2f}"
                            )

                            if score > best_score:
                                candidate_model_id = model_id
                                selected_client = client
                                best_score = score

                if candidate_model_id is None or selected_client is None:
                    self.logger.warning("使用可能なモデルがありません")
                    # リトライまで待機
                    await asyncio.sleep(1)
                    attempts += 1
                    continue

                # 選択されたモデルでリクエストを実行
                metrics = self.model_manager.get_model_metrics(candidate_model_id)
                if not metrics:
                    self.logger.error(
                        f"モデル {candidate_model_id} のメトリクスが見つかりません"
                    )
                    return None, None, 0, 0

                await metrics.add_request(token_cost)

                start_time = time.perf_counter()
                try:
                    result = await asyncio.wait_for(
                        selected_client.execute_prompt(prompt), timeout=self.timeout
                    )
                    if result is None:
                        raise ValueError("レスポンスがNoneです")

                    latency = time.perf_counter() - start_time
                    self.logger.info(
                        f"モデル: {candidate_model_id}, レイテンシ: {latency:.2f}秒, トークンコスト: {token_cost}"
                    )

                    return candidate_model_id, result, token_cost, latency

                except asyncio.TimeoutError:
                    self.logger.error(
                        f"モデル {candidate_model_id} がタイムアウトしました"
                    )
                    metrics.record_timeout()
                    attempts += 1
                except ValueError as e:
                    self.logger.error(f"モデル {candidate_model_id} の応答エラー: {e}")
                    metrics.record_timeout()
                    attempts += 1
                except Exception as e:
                    self.logger.error(
                        f"モデル {candidate_model_id} の実行中にエラーが発生しました: {e}"
                    )
                    metrics.record_timeout()
                    attempts += 1

            except Exception as e:
                self.logger.error(f"モデル選択中にエラーが発生しました: {e}")
                attempts += 1

        # すべてのリトライに失敗
        self.logger.error(
            f"リトライ回数 {self.retry_count} 回を超えたため、処理を中止します"
        )
        return None, None, 0, 0

    def _estimate_token_cost(self, client: OpenAIClient, prompt: str) -> int:
        """
        クライアント側でトークン数を推定する
        - encoding_model がない場合は単純な文字数で近似
        """
        try:
            if not hasattr(client, "encoder") or client.encoder is None:
                return len(prompt) + 3
            else:
                return client.estimate_tokens(prompt)
        except Exception as e:
            self.logger.error(f"トークン数推定中にエラーが発生しました: {e}")
            # エラー時は安全側に多めに見積もる
            return len(prompt) * 2

    async def cancel_tasks(self) -> None:
        """進行中のタスクをキャンセルする"""
        for task in self.tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    self.logger.error(
                        f"タスクのキャンセル中にエラーが発生しました: {e}"
                    )

        # キャンセル処理を待つ
        try:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        except Exception as e:
            self.logger.error(f"タスクのクリーンアップ中にエラーが発生しました: {e}")

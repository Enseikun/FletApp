import asyncio
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TypedDict

from src.models.azure.token_observer import TokenRateLimiter


class ModelMetrics:
    """
    各モデルの状態を管理（TPM/RPM管理、平均レスポンス時間、タイムアウト状態）
    """

    def __init__(self, rate_limits_tpm: int, rate_limits_rpm: int):
        # TPM管理
        self.tpm_limiter = TokenRateLimiter(max_tpm=rate_limits_tpm)

        # RPM管理
        self.rpm_limit = rate_limits_rpm
        self.rpm_counter = 0
        self.rpm_reset_time = datetime.now()

        # 平均レスポンス時間
        self.total_latency = 0.0
        self.completed_requests = 0

        # タイムアウトによる候補からの除外
        self.disabled_until: Optional[datetime] = None

        self.lock = asyncio.Lock()

    async def can_accept_request(self, token_cost: int) -> bool:
        """
        要求を受付可能か判定
        - タイムアウト状態ではない
        - RPM制限に抵触していない
        - TPM制限を超えていない
        """
        # タイムアウト状態ではないか確認
        if self.disabled_until and datetime.now() < self.disabled_until:
            return False

        # RPM制限チェック
        now = datetime.now()
        if now >= self.rpm_reset_time + timedelta(seconds=60):
            self.rpm_reset_time = now
            self.rpm_counter = 0

        if self.rpm_counter >= self.rpm_limit:
            return False

        # TPM制限チェック
        if not await self.tpm_limiter.can_process_tokens(token_cost):
            return False

        return True

    async def add_request(self, token_cost: int) -> None:
        """
        リクエスト開始時にRPMとTPMを更新
        """
        async with self.lock:
            self.rpm_counter += 1
            await self.tpm_limiter.on_token_added(token_cost)

    async def complete_request(self, latency: float, token_cost: int) -> None:
        """
        リクエスト完了時にTPMと平均レスポンス時間を更新
        """
        async with self.lock:
            self.total_latency += latency
            self.completed_requests += 1
            await self.tpm_limiter.on_token_completed(token_cost)

    def record_timeout(self, cool_down: int = 60) -> None:
        """
        APIタイムアウトやエラー発生時に一定期間モデルを除外する
        """
        self.disabled_until = datetime.now() + timedelta(seconds=cool_down)

    def get_average_latency(self) -> float:
        """
        平均レスポンス時間を取得
        """
        if self.completed_requests == 0:
            return 0.0
        return self.total_latency / self.completed_requests

    async def get_token_availability(self) -> float:
        """
        トークン余裕度を取得 (0.0 ~ 1.0の範囲、値が大きいほど余裕がある)
        """
        current_tpm = await self.tpm_limiter.get_current_tpm()
        max_tpm = self.tpm_limiter.max_tpm

        # TPMの使用率を計算し、余裕度を返す (1.0 - 使用率)
        if max_tpm <= 0:
            return 0.0
        return 1.0 - (current_tpm / max_tpm)


class ModelConfigDict(TypedDict):
    rate_limits_tpm: int
    rate_limits_rpm: int


class ModelManager:
    """
    各モデルのトークン管理およびリクエストの実行状態を管理
    - models のキーは model_id
    - 各モデルごとにインスタンスを保持
    """

    _instance = None

    def __new__(cls, models: Dict[str, ModelConfigDict]):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, models: Dict[str, ModelConfigDict]):
        if self._initialized:
            return

        self.models: Dict[str, ModelMetrics] = {}
        for model_id, model_config in models.items():
            self.models[model_id] = ModelMetrics(
                rate_limits_tpm=model_config.get("rate_limits_tpm", 1000),
                rate_limits_rpm=model_config.get("rate_limits_rpm", 1000),
            )
        self._initialized = True

    def get_model_metrics(self, model_id: str) -> Optional[ModelMetrics]:
        """
        指定されたモデルのメトリクスを取得
        """
        return self.models.get(model_id)

    def get_all_metrics(self) -> Dict[str, ModelMetrics]:
        """
        全モデルのメトリクスを取得
        """
        return self.models

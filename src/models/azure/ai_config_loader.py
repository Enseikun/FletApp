import json
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from src.util.object_util import get_safe


class RateLimitsDict(TypedDict):
    tpm: int
    rpm: int


class MaxTokensDict(TypedDict):
    input: int
    output: int


class ModelConfigDict(TypedDict):
    model_id: str
    encoding_model: str
    max_tokens: MaxTokensDict
    rate_limits: RateLimitsDict


class ModelConfig:
    def __init__(self, config: ModelConfigDict):
        self.model_id: str = config["model_id"]
        self.encoding_model: str = config["encoding_model"]

        max_tokens = config.get("max_tokens", {})
        self.max_tokens_input: int = max_tokens.get("input", 0)
        self.max_tokens_output: int = max_tokens.get("output", 0)

        rate_limits = config.get("rate_limits", {})
        self.rate_limits_tpm: int = rate_limits.get("tpm", 0)
        self.rate_limits_rpm: int = rate_limits.get("rpm", 0)


class AIConfigLoaderDict(TypedDict, total=False):
    api_key: str
    api_base_url: str
    api_version: str
    timeout: int
    token_timeout: int
    models: List[ModelConfigDict]


class AIConfigLoader:
    def __init__(self, config_path: str = "config/ai_config.json"):
        self.config_path: Path = Path(config_path)
        self.api_key: str = ""
        self.api_base_url: str = ""
        self.api_version: str = ""
        self.timeout: int = 30
        self.token_timeout: int = 300
        self.models: List[ModelConfig] = []
        self.load_config()

    def load_config(self) -> None:
        with self.config_path.open("r", encoding="utf-8") as f:
            config: AIConfigLoaderDict = json.load(f)

        self.api_key = config.get("api_key", "")
        self.api_base_url = config.get("api_base_url", "")
        self.api_version = config.get("api_version", "")
        self.timeout = config.get("timeout", 30)
        self.token_timeout = config.get("token_timeout", 300)

        models_config: List[ModelConfigDict] = config.get("models", [])
        self.models = [ModelConfig(model_config) for model_config in models_config]

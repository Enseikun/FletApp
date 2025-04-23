from typing import Any, Dict, List, Optional

import litellm
from litellm.utils import token_counter

from src.core.logger import get_logger
from src.models.azure.ai_config_loader import AIConfigLoader


class LiteLLMClient:
    def __init__(self, system_prompt: str, model_id: str):
        config = AIConfigLoader()
        self.api_key = config.api_key
        self.api_base_url = config.api_base_url
        self.api_version = config.api_version
        self.model_id = model_id
        self.timeout = config.timeout

        # LiteLLMの設定
        litellm.api_key = self.api_key
        litellm.api_base = self.api_base_url
        litellm.api_version = self.api_version

        # モデルプロバイダーに基づいた設定
        if "azure" in self.model_id.lower():
            # Azure OpenAIの場合
            litellm.azure_api_key = self.api_key
            litellm.azure_api_base = self.api_base_url
            litellm.azure_api_version = self.api_version
        elif "claude" in self.model_id.lower():
            # Azure上のClaudeの場合
            self.mapped_model = f"azure/{self.model_id}"
        elif "gemini" in self.model_id.lower():
            # Azure上のGeminiの場合
            self.mapped_model = f"azure/{self.model_id}"
        else:
            # デフォルトはAzure OpenAIとして扱う
            self.mapped_model = self.model_id

        self.system_prompt = system_prompt

        # システムプロンプトのトークン数を計算
        self.system_prompt_tokens = token_counter.count_tokens(
            model=self.model_id,
            messages=[{"role": "system", "content": self.system_prompt}],
        )

        self.logger = get_logger()

    def estimate_tokens(self, prompt: str) -> int:
        # ユーザープロンプトのトークン数を計算
        user_prompt_tokens = token_counter.count_tokens(
            model=self.model_id, messages=[{"role": "user", "content": prompt}]
        )

        # システムプロンプトとユーザープロンプトの合計を返す
        # +3は役割タグのための追加トークン（OpenAIの場合）
        return self.system_prompt_tokens + user_prompt_tokens + 3

    async def execute_prompt(self, prompt: str) -> Optional[str]:
        if not prompt:
            return None

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]

        model_to_use = getattr(self, "mapped_model", self.model_id)

        try:
            response = await litellm.acompletion(
                model=model_to_use,
                messages=messages,
                temperature=0.0,
                timeout=self.timeout,
            )

            return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"LiteLLM APIエラー: {e}")
            return None

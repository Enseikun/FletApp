from typing import Any, Dict, List, Optional

import openai
from tiktoken import encoding_for_model

from src.core.logger import get_logger
from src.models.azure.ai_config_loader import AIConfigLoader


class OpenAIClient:
    def __init__(self, system_prompt: str, model_id: str):
        config = AIConfigLoader()
        self.api_key = config.api_key
        self.api_base_url = config.api_base_url
        self.api_version = config.api_version
        self.model_id = model_id
        self.timeout = config.timeout

        # モデルの設定を見つける
        encoding_model = None
        for model in config.models:
            if model.model_id == model_id:
                encoding_model = model.encoding_model
                break

        self.encoder = encoding_for_model(encoding_model) if encoding_model else None

        self.client = openai.AsyncAzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.api_base_url,
            model=self.model_id,
        )

        self.system_prompt = system_prompt
        self.system_prompt_tokens = (
            len(self.encoder.encode(self.system_prompt)) if self.encoder else 0
        )

        self.logger = get_logger()

    def estimate_tokens(self, prompt: str) -> int:
        return (
            self.system_prompt_tokens + len(self.encoder.encode(prompt)) + 3
            if self.encoder
            else 0
        )

    async def execute_prompt(self, prompt: str) -> Optional[str]:
        if not prompt:
            return None

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=0.0,
                timeout=self.timeout,
            )

            return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"OpenAI APIエラー: {e}")
            return None

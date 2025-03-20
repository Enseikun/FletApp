from typing import Any, Dict, List, Optional

import openai
from tiktoken import encoding_for_model

from src.core.logger import get_logger
from src.models.azure.ai_config import AIConfig


class OpenAIClient:
    def __init__(self, system_prompt: str):
        config = AIConfig.init()
        self.api_key = config.api_key
        self.api_base_url = config.api_base_url
        self.api_version = config.api_version
        self.model_id = config.model_id
        self.encoder = encoding_for_model(config.encoding_model)

        self.client = openai.AsyncAzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.api_base_url,
            # model=self.model_id,
        )

        self.system_prompt = system_prompt
        self.system_prompt_tokens = len(self.encoder.encode(self.system_prompt))

        self.logger = get_logger()

    def estimate_tokens(self, prompt: str) -> int:
        return self.system_prompt_tokens + len(self.encoder.encode(prompt)) + 3

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
                timeout=30,
            )

            return response.choices[0].message.content

        except Exception as e:
            self.logger.error(f"OpenAI APIエラー: {e}")
            return None

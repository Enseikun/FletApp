import re
from typing import Any, Dict, Optional

import aiohttp
from aiohttp.client_exceptions import (
    ClientConnectionError,
    ClientError,
    ClientResponseError,
    ClientTimeout,
)

from src.core.logger import get_logger


class AIClient:
    """
    model_idに応じてリクエストモデルを切り替える
    """

    GPT_PATH_TMPL = (
        "/openai/deployments/{deployment_id}/chat/completions?api-version={api_version}"
    )
    CLAUDE_PATH = "/claude"
    GEMINI_PATH = "/gemini"

    def __init__(
        self, api_key: str, endpoint: str, api_version: str = "2023-03-01-preview"
    ):
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.api_version = api_version
        self.logger = get_logger()
        self.session = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """セッションが存在しない場合は新しく作成する"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self) -> None:
        """セッションを閉じる"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def send_prompt(
        self, model_id: str, system_prompt: str, user_prompt: str, timeout: int = 30
    ) -> Optional[str]:
        model_id_lower = model_id.lower()
        try:
            if "gpt" in model_id_lower or re.match(r"^o\d+(-|mini)", model_id_lower):
                return await self._send_gpt(
                    model_id, system_prompt, user_prompt, timeout
                )
            elif "claude" in model_id_lower:
                return await self._send_claude(
                    model_id, system_prompt, user_prompt, timeout
                )
            elif "gemini" in model_id_lower:
                return await self._send_gemini(
                    model_id, system_prompt, user_prompt, timeout
                )
            else:
                error_msg = f"サポートされていないモデルです: {model_id}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
        except Exception as e:
            self.logger.error(
                f"モデル {model_id} でのリクエスト処理中にエラーが発生しました: {e}"
            )
            raise

    async def _send_gpt(
        self, model_id: str, system_prompt: str, user_prompt: str, timeout: int = 30
    ) -> str:
        url = self.endpoint + self.GPT_PATH_TMPL.format(
            deployment_id=model_id, api_version=self.api_version
        )
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
        }
        data = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
        }
        try:
            self.logger.debug(f"GPTモデルへリクエスト送信: {model_id}")
            session = await self._ensure_session()
            timeout_obj = aiohttp.ClientTimeout(total=timeout)

            async with session.post(
                url, headers=headers, json=data, timeout=timeout_obj
            ) as response:
                response.raise_for_status()
                response_data = await response.json()
                return response_data["choices"][0]["message"]["content"]
        except ClientTimeout:
            error_msg = f"GPTモデル {model_id} へのリクエストがタイムアウトしました"
            self.logger.error(error_msg)
            raise TimeoutError(error_msg)
        except ClientResponseError as e:
            error_msg = (
                f"GPTモデル {model_id} へのリクエスト中にHTTPエラーが発生しました: {e}"
            )
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        except (ClientError, ClientConnectionError) as e:
            error_msg = f"GPTモデル {model_id} への接続中にエラーが発生しました: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"GPTモデル {model_id} へのリクエスト中に予期せぬエラーが発生しました: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

    async def _send_claude(
        self, model_id: str, system_prompt: str, user_prompt: str, timeout: int = 30
    ) -> str:
        url = self.endpoint + self.CLAUDE_PATH
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/json",
        }
        data = {
            "InputBody": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "modelID": model_id,
            "temperature": 0.7,
            "thinking": {"type": "disabled", "budget_tokens": 0},
        }
        try:
            self.logger.debug(f"Claudeモデルへリクエスト送信: {model_id}")
            session = await self._ensure_session()
            timeout_obj = aiohttp.ClientTimeout(total=timeout)

            async with session.post(
                url, headers=headers, json=data, timeout=timeout_obj
            ) as response:
                response.raise_for_status()
                response_data = await response.json()
                return response_data["content"][-1]["text"]
        except ClientTimeout:
            error_msg = f"Claudeモデル {model_id} へのリクエストがタイムアウトしました"
            self.logger.error(error_msg)
            raise TimeoutError(error_msg)
        except ClientResponseError as e:
            error_msg = f"Claudeモデル {model_id} へのリクエスト中にHTTPエラーが発生しました: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        except (ClientError, ClientConnectionError) as e:
            error_msg = f"Claudeモデル {model_id} への接続中にエラーが発生しました: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Claudeモデル {model_id} へのリクエスト中に予期せぬエラーが発生しました: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

    async def _send_gemini(
        self, model_id: str, system_prompt: str, user_prompt: str, timeout: int = 30
    ) -> str:
        url = self.endpoint + self.GEMINI_PATH
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Content-Type": "application/json",
        }
        data = {
            "inputBody": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "modelID": model_id,
            "temperature": 0.7,
        }
        try:
            self.logger.debug(f"Geminiモデルへリクエスト送信: {model_id}")
            session = await self._ensure_session()
            timeout_obj = aiohttp.ClientTimeout(total=timeout)

            async with session.post(
                url, headers=headers, json=data, timeout=timeout_obj
            ) as response:
                response.raise_for_status()
                try:
                    # 返答がjsonの場合
                    response_data = await response.json()
                    return response_data.get("candidates", [{}])[0].get(
                        "content", await response.text()
                    )
                except Exception as e:
                    self.logger.warning(
                        f"GeminiレスポンスのJSON解析に失敗しました。テキストとして処理します: {e}"
                    )
                    # テキストの場合
                    return await response.text()
        except ClientTimeout:
            error_msg = f"Geminiモデル {model_id} へのリクエストがタイムアウトしました"
            self.logger.error(error_msg)
            raise TimeoutError(error_msg)
        except ClientResponseError as e:
            error_msg = f"Geminiモデル {model_id} へのリクエスト中にHTTPエラーが発生しました: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        except (ClientError, ClientConnectionError) as e:
            error_msg = f"Geminiモデル {model_id} への接続中にエラーが発生しました: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Geminiモデル {model_id} へのリクエスト中に予期せぬエラーが発生しました: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

    async def estimate_tokens(
        self, model_id: str, system_prompt: str, user_prompt: str
    ) -> int:
        # 注: これは単純な見積もりです。より正確な計算が必要な場合は改善が必要です
        total_chars = len(system_prompt) + len(user_prompt)
        self.logger.debug(
            f"モデル {model_id} のトークン数見積もり: 約 {total_chars} 文字"
        )
        return total_chars

    async def execute_prompt(self, prompt: str) -> Optional[str]:
        """
        OpenAIClientと同じインターフェースでプロンプトを実行する
        この関数により、AIClientはOpenAIClientの代替として使用可能
        """
        if not hasattr(self, "model_id") or not hasattr(self, "system_prompt"):
            self.logger.error(
                "AIClientの設定が不完全です。model_idとsystem_promptが必要です。"
            )
            return None

        try:
            return await self.send_prompt(self.model_id, self.system_prompt, prompt)
        except Exception as e:
            self.logger.error(f"プロンプト実行中にエラーが発生しました: {e}")
            return None

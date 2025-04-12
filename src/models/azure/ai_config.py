from dataclasses import dataclass
from typing import Final


@dataclass
class AIConfig:
    api_key: Final[str] = None
    api_base_url: Final[str] = None
    api_version: Final[str] = None
    model_id: Final[str] = None
    encoding_model: Final[str] = None
    timeout: Final[int] = None

    @classmethod
    def init(cls):
        return cls(
            api_key="",
            api_base_url="",
            api_version="2025-01-01-preview",
            model_id="gpt-4o",
            encoding_model="gpt-4o",
            timeout=30,
        )

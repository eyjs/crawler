# src/llm/__init__.py

from config.settings import config
from .base_client import BaseLlmClient

def get_llm_client() -> BaseLlmClient:
    """설정에 따라 적절한 LLM 클라이언트 인스턴스를 반환합니다."""
    provider = config.llm_provider.lower()

    if provider == "gemini":
        from .gemini_client import GeminiClient
        return GeminiClient()
    elif provider == "local":
        from .local_client import LocalLlmClient
        # 로컬에서 사용할 모델을 지정할 수 있습니다.
        return LocalLlmClient(model=config.local_llm_model)
    else:
        raise ValueError(f"지원하지 않는 LLM 제공자입니다: {provider}")

# 전역 클라이언트 인스턴스
llm_client = get_llm_client()
# src/llm/__init__.py (올바른 최종 버전)

from loguru import logger
from config.settings import config
from .base_client import BaseLlmClient
from .gemini_client import GeminiClient
from .local_client import LocalLlmClient

def _create_llm_client(provider: str, model_name: str, client_role: str) -> BaseLlmClient:
    """단일 LLM 클라이언트 인스턴스를 생성하는 헬퍼 함수."""
    logger.info(f"'{client_role}' 역할에 '{provider}' 제공자의 '{model_name}' 모델을 설정합니다.")
    if provider == "gemini":
        return GeminiClient(model_name=model_name)
    elif provider == "local":
        return LocalLlmClient(model=model_name)
    else:
        raise ValueError(f"지원하지 않는 LLM 제공자입니다: {provider}")

# 라우팅 LLM 클라이언트 생성
routing_llm = _create_llm_client(
    provider=config.routing_llm_provider,
    model_name=config.routing_gemini_model if config.routing_llm_provider == 'gemini' else config.analysis_local_model,
    client_role="라우팅"
)

# 분석 LLM 클라이언트 생성
analysis_llm = _create_llm_client(
    provider=config.analysis_llm_provider,
    model_name=config.routing_gemini_model if config.analysis_llm_provider == 'gemini' else config.analysis_local_model,
    client_role="분석"
)
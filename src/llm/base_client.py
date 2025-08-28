# src/llm/base_client.py

from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseLlmClient(ABC):
    """모든 LLM 클라이언트가 상속받아야 할 기본 클래스"""

    @abstractmethod
    async def evaluate_relevance_score(self, link_text: str, url: str, context: str, target_goal: str) -> float:
        """링크의 관련성 점수를 0.0 ~ 1.0 사이로 평가합니다."""
        pass

    @abstractmethod
    async def enrich_content(self, content: str, instruction_prompt: str) -> Dict[str, Any]:
        """
        주어진 텍스트 콘텐츠를 요약하고 키워드를 추출합니다.
        Returns:
            {"summary": "...", "keywords": ["...", "..."]}
        """
        pass
# src/llm/base_client.py

from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseLlmClient(ABC):
    @abstractmethod
    async def evaluate_relevance_score(self, link_text: str, url: str, context: str, target_goal: str, strategic_notes: str) -> float:
        """
        단일 링크의 관련성 점수를 0.0 ~ 1.0 사이로 평가합니다.
        """
        pass

    @abstractmethod
    async def analyze_content(self, content: str, instruction_prompt: str) -> Dict[str, Any]:
        """
        하나의 콘텐츠에서 요약, 키워드, 최종 점수를 한 번에 추출합니다.
        """
        pass

    @abstractmethod
    async def update_critique(self, previous_critique: str, crawled_summaries: str, instruction_prompt: str, site_name: str) -> str:
        """
        기존 전략과 새로운 결과를 바탕으로 고도화된 전략 노트를 생성합니다.
        """
        pass
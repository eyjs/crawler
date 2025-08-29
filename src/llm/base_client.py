# src/llm/base_client.py

from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseLlmClient(ABC):
    @abstractmethod
    async def evaluate_links_batch(self, links: List[Dict[str, str]], target_goal: str) -> List[Dict[str, Any]]:
        """
        여러 링크를 한 번에 평가하여 각 링크에 'score'를 추가한 리스트를 반환합니다.
        """
        pass

    @abstractmethod
    async def analyze_content(self, content: str, instruction_prompt: str) -> Dict[str, Any]:
        """
        하나의 콘텐츠에서 요약, 키워드, 최종 점수를 한 번에 추출합니다.
        """
        pass
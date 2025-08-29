# src/llm/local_client.py

import ollama
import re
import json
from loguru import logger
from typing import Dict, Any, List

from config.settings import config
from .base_client import BaseLlmClient

class LocalLlmClient(BaseLlmClient):
    def __init__(self, model: str):
        self.client = ollama.AsyncClient()
        self.model = model
        logger.info(f"✅ 로컬 LLM 클라이언트가 초기화되었습니다 (모델: {self.model})")

    async def evaluate_links_batch(self, links: List[Dict[str, str]], target_goal: str) -> List[Dict[str, Any]]:
        """여러 링크를 한 번에 평가하여 각 링크에 'score'를 추가한 리스트를 반환합니다."""
        links_json_str = json.dumps(links, ensure_ascii=False, indent=2)

        prompt = config.local_batch_link_eval_prompt.format(
            target_goal=target_goal,
            links_json_str=links_json_str
        )

        try:
            response = await self.client.generate(model=self.model, prompt=prompt, stream=False, format="json")
            response_text = response['response'].strip()
            scored_links = json.loads(response_text)

            # Ollama가 가끔 score 필드를 누락하는 경우가 있어 안정성 확보
            for i, link in enumerate(links):
                if 'score' not in scored_links[i]:
                    scored_links[i]['score'] = 0.0

            return scored_links
        except Exception as e:
            logger.error(f"로컬 LLM 링크 일괄 평가 실패: {e}")
            return [dict(link, score=0.0) for link in links]

    async def analyze_content(self, content: str, instruction_prompt: str) -> Dict[str, Any]:
        """하나의 콘텐츠에서 요약, 키워드, 최종 점수를 한 번에 추출합니다."""
        prompt = config.local_combined_analysis_prompt.format(
            instruction_prompt=instruction_prompt,
            content=content[:4000]
        )

        try:
            response = await self.client.generate(model=self.model, prompt=prompt, stream=False, format="json")
            response_text = response['response'].strip()
            analysis_result = json.loads(response_text)

            # Ollama가 가끔 특정 키를 누락하는 경우가 있어 안정성 확보
            if 'summary' not in analysis_result: analysis_result['summary'] = ""
            if 'keywords' not in analysis_result: analysis_result['keywords'] = []
            if 'relevance_score' not in analysis_result: analysis_result['relevance_score'] = 0.0

            return analysis_result
        except Exception as e:
            logger.error(f"로컬 LLM 콘텐츠 통합 분석 실패: {e}")
            return {"summary": "", "keywords": [], "relevance_score": 0.0}
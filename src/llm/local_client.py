# src/llm/local_client.py

import asyncio
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

    async def evaluate_relevance_score(self, link_text: str, url: str, context: str, target_goal: str, strategic_notes: str) -> float:
        prompt = config.local_link_eval_prompt.format(
            target_goal=target_goal,
            strategic_notes=strategic_notes or "No specific strategies yet.",
            link_text=link_text,
            url=url,
            context=context[:200]
        )
        try:
            response = await self.client.generate(model=self.model, prompt=prompt, stream=False)
            score_text = response['response'].strip()
            numbers = re.findall(r'\d+\.?\d*', score_text)
            if numbers:
                return max(0.0, min(1.0, float(numbers[0])))
            logger.warning(f"로컬 LLM 링크 점수 파싱 실패: {score_text}")
            return 0.0
        except Exception as e:
            logger.error(f"로컬 LLM 링크 평가 실패: {url} | {e}")
            return 0.0

    async def analyze_content(self, content: str, instruction_prompt: str) -> Dict[str, Any]:
        prompt = config.local_combined_analysis_prompt.format(
            instruction_prompt=instruction_prompt,
            content=content[:4000]
        )
        try:
            response = await self.client.generate(model=self.model, prompt=prompt, stream=False, format="json")
            response_text = response['response'].strip()
            analysis_result = json.loads(response_text)
            if 'summary' not in analysis_result: analysis_result['summary'] = ""
            if 'keywords' not in analysis_result: analysis_result['keywords'] = []
            if 'relevance_score' not in analysis_result: analysis_result['relevance_score'] = 0.0
            return analysis_result
        except Exception as e:
            logger.error(f"로컬 LLM 콘텐츠 통합 분석 실패: {e}")
            return {"summary": "", "keywords": [], "relevance_score": 0.0}

    async def update_critique(self, previous_critique: str, crawled_summaries: str, instruction_prompt: str, site_name: str) -> str:
        prompt = config.local_critique_update_prompt.format(
            site_name=site_name,
            instruction_prompt=instruction_prompt,
            previous_critique=previous_critique or "This is the first crawl for this site. No previous notes.",
            crawled_summaries=crawled_summaries[:4000]
        )
        try:
            response = await self.client.generate(model=self.model, prompt=prompt, stream=False)
            return response['response'].strip()
        except Exception as e:
            logger.error(f"로컬 LLM 자기 교정 노트 생성 실패: {e}")
            return "피드백 생성 중 오류가 발생했습니다."

    async def evaluate_links_batch(self, links: List[Dict[str, str]], target_goal: str, strategic_notes: str) -> List[Dict[str, Any]]:
        """주어진 링크 목록을 일괄적으로 평가하여 각 링크에 대한 점수를 반환합니다."""
        tasks = []
        for link in links:
            task = self.evaluate_relevance_score(
                link_text=link.get('text', ''),
                url=link.get('url', ''),
                context="",
                target_goal=target_goal,
                strategic_notes=strategic_notes
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        scored_links = []
        for link, result in zip(links, results):
            score = 0.0
            if isinstance(result, Exception):
                logger.error(f"링크 평가 중 예외 발생: {link.get('url')} | {result}")
            else:
                score = result
            
            scored_links.append({
                "url": link.get('url'),
                "text": link.get('text'),
                "score": score
            })
        return scored_links
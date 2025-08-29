# src/llm/local_client.py

import ollama
import re
import json
from loguru import logger
from typing import Dict, Any

from config.settings import config
from .base_client import BaseLlmClient

class LocalLlmClient(BaseLlmClient):
    def __init__(self, model: str):
        self.client = ollama.AsyncClient()
        self.model = model
        logger.info(f"✅ 로컬 LLM 클라이언트가 초기화되었습니다 (모델: {self.model})")

    async def evaluate_relevance_score(self, link_text: str, url: str, context: str, target_goal: str) -> float:
        prompt = config.local_link_eval_prompt.format(
            target_goal=target_goal,
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
            logger.error(f"로컬 LLM 링크 평가 실패: {e}")
            return 0.0

    async def enrich_content(self, content: str, instruction_prompt: str) -> Dict[str, Any]:
        prompt = config.local_content_enrich_prompt.format(
            instruction_prompt=instruction_prompt,
            content=content[:4000]
        )
        try:
            response = await self.client.generate(model=self.model, prompt=prompt, stream=False, format="json")
            json_text = response['response'].strip()
            data = json.loads(json_text)
            return {"summary": data.get("summary", ""), "keywords": data.get("keywords", [])}
        except Exception as e:
            logger.error(f"로컬 LLM 콘텐츠 강화 실패: {e}")
            return {"summary": "", "keywords": []}

    async def score_content_relevance(self, content: str, instruction_prompt: str) -> float:
        prompt = config.local_content_score_prompt.format(
            instruction_prompt=instruction_prompt,
            content=content[:4000]
        )
        try:
            response = await self.client.generate(model=self.model, prompt=prompt, stream=False)
            score_text = response['response'].strip()
            numbers = re.findall(r'\d+\.?\d*', score_text)
            if numbers:
                return max(0.0, min(1.0, float(numbers[0])))
            logger.warning(f"로컬 LLM 콘텐츠 점수 파싱 실패: {score_text}")
            return 0.0
        except Exception as e:
            logger.error(f"로컬 LLM 콘텐츠 점수 평가 실패: {e}")
            return 0.0
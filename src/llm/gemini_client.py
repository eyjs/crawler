# src/llm/gemini_client.py

import asyncio
import re
import json
from loguru import logger
import google.generativeai as genai
from typing import Dict, Any, List

from config.settings import config
from .base_client import BaseLlmClient

class GeminiClient(BaseLlmClient):
    def __init__(self, model_name: str):
        self.model_name = model_name
        if not config.gemini_api_key or "여기에" in config.gemini_api_key:
            raise ValueError("Gemini API 키가 .env 파일에 설정되지 않았습니다.")
        genai.configure(api_key=config.gemini_api_key)
        self.model = genai.GenerativeModel(self.model_name)
        self.generation_config = genai.types.GenerationConfig(
            max_output_tokens=config.gemini_max_tokens,
            temperature=0.2,
        )
        logger.info(f"✅ Gemini 클라이언트가 초기화되었습니다 (모델: {self.model_name})")

    def _generate_sync(self, prompt: str):
        return self.model.generate_content(prompt, generation_config=self.generation_config)

    async def evaluate_relevance_score(self, link_text: str, url: str, context: str, target_goal: str, strategic_notes: str) -> float:
        prompt = config.gemini_link_eval_prompt.format(
            target_goal=target_goal,
            strategic_notes=strategic_notes or "No specific strategies yet.",
            link_text=link_text,
            url=url,
            context=context[:200]
        )
        try:
            response = await asyncio.to_thread(self._generate_sync, prompt)
            score_text = response.text.strip()
            numbers = re.findall(r'\d+\.?\d*', score_text)
            if numbers:
                return max(0.0, min(1.0, float(numbers[0])))
            logger.warning(f"Gemini 링크 점수 파싱 실패: {score_text}")
            return 0.0
        except Exception as e:
            logger.error(f"Gemini 링크 평가 실패: {url} | {e}")
            return 0.0

    async def analyze_content(self, content: str, instruction_prompt: str) -> Dict[str, Any]:
        prompt = config.gemini_combined_analysis_prompt.format(
            instruction_prompt=instruction_prompt,
            content=content[:8000]
        )
        try:
            response = await asyncio.to_thread(self._generate_sync, prompt)
            response_text = response.text.strip().replace("```json", "").replace("```", "")
            analysis_result = json.loads(response_text)
            return analysis_result
        except Exception as e:
            logger.error(f"Gemini 콘텐츠 통합 분석 실패: {e}")
            return {"summary": "", "keywords": [], "relevance_score": 0.0}

    async def update_critique(self, previous_critique: str, crawled_summaries: str, instruction_prompt: str, site_name: str) -> str:
        prompt = config.gemini_critique_update_prompt.format(
            site_name=site_name,
            instruction_prompt=instruction_prompt,
            previous_critique=previous_critique or "This is the first crawl for this site. No previous notes.",
            crawled_summaries=crawled_summaries[:8000]
        )
        try:
            response = await asyncio.to_thread(self._generate_sync, prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini 자기 교정 노트 생성 실패: {e}")
            return "피드백 생성 중 오류가 발생했습니다."
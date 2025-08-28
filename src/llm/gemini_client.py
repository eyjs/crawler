# src/llm/gemini_client.py

import asyncio
import re
import json
from loguru import logger
import google.generativeai as genai
from typing import Dict, Any

from config.settings import config
from src.llm.base_client import BaseLlmClient

class GeminiClient(BaseLlmClient):
    """Gemini API 비동기 클라이언트"""

    def __init__(self):
        genai.configure(api_key=config.gemini_api_key)
        self.model = genai.GenerativeModel(config.gemini_model)
        self.generation_config = genai.types.GenerationConfig(
            max_output_tokens=config.gemini_max_tokens,
            temperature=0.2,
        )
        logger.info(f"✅ Gemini 클라이언트가 초기화되었습니다 (모델: {config.gemini_model})")

    def _generate_sync(self, prompt: str):
        return self.model.generate_content(
            prompt,
            generation_config=self.generation_config
        )

    async def evaluate_relevance_score(self, link_text: str, url: str, context: str, target_goal: str) -> float:
        # ... (기존 코드와 동일, 변경 없음)
        prompt = f"""Analyze the relevance of the following link to the CRAWLING GOAL. Provide a score from 0.0 (not relevant) to 1.0 (highly relevant). CRAWLING GOAL: "{target_goal}". LINK DATA: - Link Text: "{link_text}" - URL: "{url}" - Context: "{context[:200]}...". Your response MUST be only a single floating-point number (e.g., 0.85)."""
        try:
            response_text = await asyncio.to_thread(self._generate_sync, prompt)
            score_text = response_text.text.strip()
            numbers = re.findall(r'\d+\.?\d*', score_text)
            if numbers:
                score = float(numbers[0])
                return max(0.0, min(1.0, score))
            else:
                logger.warning(f"Gemini 점수 파싱 실패: {score_text}")
                return 0.0
        except Exception as e:
            logger.error(f"Gemini API 호출 실패: {e}")
            return 0.0

    async def enrich_content(self, content: str, instruction_prompt: str) -> Dict[str, Any]:
        """콘텐츠 요약 및 키워드 추출"""
        prompt = f"""
        Analyze the following text, keeping the main goal in mind: "{instruction_prompt}".

        TEXT:
        "{content[:4000]}..."

        TASKS:
        1. Summarize the text in 3 concise Korean sentences.
        2. Extract 7-10 relevant keywords in Korean.

        Provide the output in a JSON object with two keys: "summary" and "keywords".
        Example: {{"summary": "...", "keywords": ["...", "..."]}}
        """
        try:
            response = await asyncio.to_thread(self._generate_sync, prompt)
            json_text = response.text.strip().replace("```json", "").replace("```", "")
            data = json.loads(json_text)
            return {
                "summary": data.get("summary", ""),
                "keywords": data.get("keywords", [])
            }
        except Exception as e:
            logger.error(f"Gemini 콘텐츠 강화 실패: {e}")
            return {"summary": "", "keywords": []}
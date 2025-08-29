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
        """동기식 API 호출을 위한 내부 헬퍼 함수"""
        return self.model.generate_content(prompt, generation_config=self.generation_config)

    async def evaluate_links_batch(self, links: List[Dict[str, str]], target_goal: str) -> List[Dict[str, Any]]:
        """여러 링크를 한 번에 평가하여 각 링크에 'score'를 추가한 리스트를 반환합니다."""
        # 링크 리스트를 JSON 문자열로 변환
        links_json_str = json.dumps(links, ensure_ascii=False, indent=2)

        # 설정 파일에서 일괄 처리용 프롬프트 템플릿을 가져와 사용
        prompt = config.gemini_batch_link_eval_prompt.format(
            target_goal=target_goal,
            links_json_str=links_json_str
        )

        try:
            # --- 실제 LLM 호출 로직 ---
            response = await asyncio.to_thread(self._generate_sync, prompt)
            response_text = response.text.strip().replace("```json", "").replace("```", "")
            scored_links = json.loads(response_text)
            # --------------------------
            return scored_links
        except Exception as e:
            logger.error(f"Gemini 링크 일괄 평가 실패: {e}")
            # 실패 시, 원본 링크 리스트에 score=0.0을 추가하여 반환
            return [dict(link, score=0.0) for link in links]

    async def analyze_content(self, content: str, instruction_prompt: str) -> Dict[str, Any]:
        """하나의 콘텐츠에서 요약, 키워드, 최종 점수를 한 번에 추출합니다."""
        # 설정 파일에서 통합 분석용 프롬프트 템플릿을 가져와 사용
        prompt = config.gemini_combined_analysis_prompt.format(
            instruction_prompt=instruction_prompt,
            content=content[:4000]
        )

        try:
            # --- 실제 LLM 호출 로직 ---
            response = await asyncio.to_thread(self._generate_sync, prompt)
            response_text = response.text.strip().replace("```json", "").replace("```", "")
            analysis_result = json.loads(response_text)
            # --------------------------
            return analysis_result
        except Exception as e:
            logger.error(f"Gemini 콘텐츠 통합 분석 실패: {e}")
            return {"summary": "", "keywords": [], "relevance_score": 0.0}
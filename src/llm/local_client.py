# src/llm/local_client.py

import ollama
import re
import json
from loguru import logger
from typing import Dict, Any

from src.llm.base_client import BaseLlmClient

class LocalLlmClient(BaseLlmClient):
    """로컬 LLM (Ollama) 클라이언트"""

    def __init__(self, model: str = 'llama3'):
        self.client = ollama.AsyncClient()
        self.model = model
        logger.info(f"✅ 로컬 LLM 클라이언트가 초기화되었습니다 (모델: {self.model})")

    async def evaluate_relevance_score(self, link_text: str, url: str, context: str, target_goal: str) -> float:
        # ... (기존 코드와 동일, 변경 없음)
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>You are an intelligent web crawler agent. Your task is to evaluate the relevance of a given link to a specific goal. Respond with a single floating-point number between 0.0 and 1.0, where 1.0 is highly relevant. Your response MUST be only the number. For example: 0.85<|eot_id|><|start_header_id|>user<|end_header_id|>CRAWLING GOAL: "{target_goal}". LINK DATA: - Link Text: "{link_text}" - URL: "{url}" - Context: "{context[:200]}...". Based on the goal, what is the relevance score of this link?<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
        try:
            response = await self.client.generate(model=self.model, prompt=prompt, stream=False)
            score_text = response['response'].strip()
            numbers = re.findall(r'\d+\.?\d*', score_text)
            if numbers:
                score = float(numbers[0])
                return max(0.0, min(1.0, score))
            else:
                logger.warning(f"로컬 LLM 점수 파싱 실패: {score_text}")
                return 0.0
        except Exception as e:
            logger.error(f"로컬 LLM 호출 실패: {e}")
            return 0.0

    async def enrich_content(self, content: str, instruction_prompt: str) -> Dict[str, Any]:
        """콘텐츠 요약 및 키워드 추출"""
        prompt = f"""
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>
        You are an expert text analyst. Your task is to summarize a given text and extract keywords.
        Provide the output as a valid JSON object with two keys: "summary" (a 3-sentence summary in Korean) and "keywords" (a list of 7-10 Korean keywords).
        Example: {{"summary": "...", "keywords": ["...", "..."]}}
        Your response MUST be only the JSON object.<|eot_id|>

        <|start_header_id|>user<|end_header_id|>
        Main Goal: "{instruction_prompt}"

        Text to analyze:
        "{content[:4000]}..."

        Analyze the text and provide the JSON output.<|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>
        """
        try:
            response = await self.client.generate(model=self.model, prompt=prompt, stream=False, format="json")
            json_text = response['response'].strip()
            data = json.loads(json_text)
            return {
                "summary": data.get("summary", ""),
                "keywords": data.get("keywords", [])
            }
        except Exception as e:
            logger.error(f"로컬 LLM 콘텐츠 강화 실패: {e}")
            return {"summary": "", "keywords": []}
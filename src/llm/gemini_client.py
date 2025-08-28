"""
Gemini API 클라이언트
"""
import asyncio
import json
from typing import Optional, Dict, Any
import google.generativeai as genai
from loguru import logger
from config.settings import config

class GeminiClient:
    """Gemini API 비동기 클라이언트"""
    
    def __init__(self):
        """Gemini 클라이언트 초기화"""
        genai.configure(api_key=config.gemini_api_key)
        self.model = genai.GenerativeModel(config.gemini_model)
        self.generation_config = genai.types.GenerationConfig(
            max_output_tokens=config.gemini_max_tokens,
            temperature=0.1,  # 일관된 응답을 위해 낮은 온도
        )
        logger.info(f"Gemini 클라이언트 초기화 완료 - 모델: {config.gemini_model}")
    
    async def generate_text_async(self, prompt: str) -> str:
        """비동기 텍스트 생성"""
        try:
            # Gemini는 기본적으로 동기식이므로 asyncio.to_thread로 비동기화
            response = await asyncio.to_thread(
                self._generate_sync,
                prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API 호출 실패: {e}")
            raise
    
    def _generate_sync(self, prompt: str):
        """동기식 생성 (내부 메서드)"""
        return self.model.generate_content(
            prompt,
            generation_config=self.generation_config
        )
    
    async def evaluate_relevance_score(self, link_text: str, url: str, context: str, target_goal: str) -> float:
        """링크 관련성 점수 평가"""
        prompt = f"""
        크롤링 목표: "{target_goal}"
        
        다음 링크가 위 목표와 얼마나 관련이 있는지 0.0~1.0 점수로 평가해주세요:
        - 링크 텍스트: "{link_text}"
        - URL: "{url}"
        - 주변 맥락: "{context[:200]}..."
        
        점수만 숫자로 답변하세요 (예: 0.85)
        """
        
        try:
            response = await self.generate_text_async(prompt)
            # 응답에서 숫자만 추출
            score_text = response.strip()
            
            # 숫자가 아닌 문자 제거
            import re
            numbers = re.findall(r'\d+\.?\d*', score_text)
            
            if numbers:
                score = float(numbers[0])
                # 0~1 범위로 제한
                return max(0.0, min(1.0, score))
            else:
                logger.warning(f"점수 파싱 실패: {score_text}")
                return 0.0
                
        except Exception as e:
            logger.error(f"관련성 평가 실패: {e}")
            return 0.0

# 전역 클라이언트 인스턴스
gemini_client = GeminiClient()
import json
import logging
import ollama
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Dict, Any

from config.settings import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s')
logger = logging.getLogger(__name__)

class LlmClient:
    """
    config/settings.py를 기반으로 Ollama와 Gemini를 지원하며,
    2단계 검증(게이트키퍼) 로직을 포함한 최종 LLM 클라이언트.
    """
    def __init__(self):
        self.provider = config.llm_provider
        self.client = None
        self.model_name = ""
        logger.info(f"LLM Provider: '{self.provider}'")
        if self.provider == "local":
            self.model_name = config.analysis_local_model
            self.client = ollama.AsyncClient()
            logger.info(f"✅ Ollama 클라이언트가 초기화되었습니다 (Model: {self.model_name})")
        elif self.provider == "gemini":
            self.model_name = config.gemini_model
            if not config.gemini_api_key:
                raise ValueError("LLM_PROVIDER가 'gemini'일 경우, GEMINI_API_KEY가 반드시 필요합니다.")
            genai.configure(api_key=config.gemini_api_key)
            self.gemini_generation_config = {"response_mime_type": "application/json"}
            self.client = genai.GenerativeModel(self.model_name)
            logger.info(f"✅ Google Generative AI 클라이언트가 초기화되었습니다 (Model: {self.model_name})")
        else:
            raise ValueError(f"지원하지 않는 LLM_PROVIDER입니다: {self.provider}. 'local' 또는 'gemini'를 사용하세요.")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def is_content_relevant(self, text: str, instruction_prompt: str) -> bool:
        """ [신규] '게이트키퍼' 역할을 수행하여 콘텐츠의 관련성 여부를 빠르게 판단합니다. """
        prompt = ""
        # 빠른 판단을 위해 텍스트 일부만 사용
        content_snippet = text[:1500]
        if self.provider == "local":
            prompt = config.local_relevance_check_prompt.format(
                instruction_prompt=instruction_prompt, content=content_snippet
            )
        elif self.provider == "gemini":
            prompt = config.gemini_relevance_check_prompt.format(
                instruction_prompt=instruction_prompt, content=content_snippet
            )

        try:
            if self.provider == "local":
                response = await self.client.chat(model=self.model_name, messages=[{'role': 'user', 'content': prompt}])
                answer = response['message']['content'].strip().upper()
            elif self.provider == "gemini":
                # JSON 모드가 아닌 일반 텍스트로 YES/NO 답변을 받음
                response = await self.client.generate_content_async(prompt)
                answer = response.text.strip().upper()

            return "YES" in answer
        except Exception as e:
            logger.error(f"LLM 관련성 검사 실패: {e}")
            return False # 실패 시에는 관련 없는 것으로 간주하여 비용 낭비 방지

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def evaluate_and_enhance_content(self, text: str, instruction_prompt: str) -> Dict[str, Any]:
        """ [기존] 관련성이 확인된 콘텐츠에 대해 심층 분석을 수행합니다. """
        prompt = ""
        if self.provider == "local":
            prompt = config.local_combined_analysis_prompt.format(instruction_prompt=instruction_prompt, content=text[:4000])
        elif self.provider == "gemini":
            prompt = config.gemini_combined_analysis_prompt.format(instruction_prompt=instruction_prompt, content=text[:8000])

        content_str = ""
        try:
            if self.provider == "local":
                messages = [{'role': 'user', 'content': prompt}]
                response = await self.client.chat(model=self.model_name, messages=messages, format="json")
                content_str = response['message']['content']
            elif self.provider == "gemini":
                response = await self.client.generate_content_async(
                    prompt,
                    generation_config=self.gemini_generation_config
                )
                content_str = response.text

            result = json.loads(content_str)
            result['relevance_score'] = float(result.get('relevance_score', 0.0))
            result.setdefault('summary', "요약 생성 실패")
            if not isinstance(result.get('keywords'), list): result['keywords'] = []
            result.setdefault('language', "unknown")
            return result
        except Exception as e:
            logger.error(f"LLM 콘텐츠 분석 실패 ({self.provider}): {e}", exc_info=True)
            return {"summary": "콘텐츠 처리 중 오류 발생", "keywords": [], "relevance_score": 0.0, "language": "unknown"}

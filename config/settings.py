# config/settings.py

"""
환경설정 관리 모듈
"""
import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

@dataclass
class CrawlerConfig:
    """크롤러 설정 클래스"""

    # Gemini 설정
    gemini_api_key: str
    gemini_model: str = "gemini-1.5-flash"
    gemini_max_tokens: int = 1000

    # LLM Provider 설정
    llm_provider: str = "local"
    local_llm_model: str = "llama3"

    # 크롤링 설정
    max_pages_per_session: int = 50
    relevance_threshold: float = 0.7
    request_delay: float = 1.0
    max_concurrent_requests: int = 5
    user_agent: str = "LLM-Crawler-Agent/1.0"

    # 타임아웃 설정
    page_load_timeout: int = 30
    http_timeout: int = 15

    # 메시지 큐 설정
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_queue: str = "crawler_results"

    # 로깅 설정
    log_level: str = "INFO"
    log_file: str = "logs/crawler.log"

    # 환경 설정
    environment: str = "development"
    debug: bool = True

    @classmethod
    def from_env(cls) -> 'CrawlerConfig':
        """환경변수에서 설정 로드"""
        return cls(
            # Gemini 설정
            gemini_api_key=os.getenv('GEMINI_API_KEY', ''),
            gemini_model=os.getenv('GEMINI_MODEL', 'gemini-1.5-flash'),
            gemini_max_tokens=int(os.getenv('GEMINI_MAX_TOKENS', '1000')),

            # LLM Provider 설정
            llm_provider=os.getenv('LLM_PROVIDER', 'local'),
            local_llm_model=os.getenv('LOCAL_LLM_MODEL', 'llama3'),

            # 크롤링 설정
            max_pages_per_session=int(os.getenv('MAX_PAGES_PER_SESSION', '50')),
            relevance_threshold=float(os.getenv('RELEVANCE_THRESHOLD', '0.7')),
            request_delay=float(os.getenv('REQUEST_DELAY', '1.0')),
            max_concurrent_requests=int(os.getenv('MAX_CONCURRENT_REQUESTS', '5')),
            user_agent=os.getenv('USER_AGENT', 'LLM-Crawler-Agent/1.0'),

            # 타임아웃 설정
            page_load_timeout=int(os.getenv('PAGE_LOAD_TIMEOUT', '30')),
            http_timeout=int(os.getenv('HTTP_TIMEOUT', '15')),

            # 메시지 큐 설정
            rabbitmq_host=os.getenv('RABBITMQ_HOST', 'localhost'),
            rabbitmq_port=int(os.getenv('RABBITMQ_PORT', '5672')),
            rabbitmq_user=os.getenv('RABBITMQ_USER', 'guest'),
            rabbitmq_password=os.getenv('RABBITMQ_PASSWORD', 'guest'),
            rabbitmq_queue=os.getenv('RABBITMQ_QUEUE', 'crawler_results'),

            # 로깅 설정
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            log_file=os.getenv('LOG_FILE', 'logs/crawler.log'),

            # 환경 설정
            environment=os.getenv('ENVIRONMENT', 'development'),
            debug=os.getenv('DEBUG', 'true').lower() == 'true',
        )

    def validate(self):
        """설정 유효성 검사"""
        if self.llm_provider == "gemini" and not self.gemini_api_key:
            raise ValueError("LLM_PROVIDER가 'gemini'일 경우 GEMINI_API_KEY가 설정되어야 합니다.")

        if self.relevance_threshold < 0 or self.relevance_threshold > 1:
            raise ValueError("RELEVANCE_THRESHOLD는 0과 1 사이의 값이어야 합니다.")

        return True

# 전역 설정 인스턴스
config = CrawlerConfig.from_env()
# config/settings.py

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

# --- Gemini용 프롬프트 템플릿 ---
GEMINI_LINK_EVAL_PROMPT = """
Analyze the relevance of the following link to the CRAWLING GOAL.
Provide a score from 0.0 (not relevant) to 1.0 (highly relevant).

CRAWLING GOAL: "{target_goal}"

LINK DATA:
- Link Text: "{link_text}"
- URL: "{url}"
- Context: "{context}"

Your response MUST be only a single floating-point number (e.g., 0.85).
"""

GEMINI_CONTENT_ENRICH_PROMPT = """
Analyze the following text, keeping the main goal in mind: "{instruction_prompt}".

TEXT:
"{content}"

TASKS:
1. Summarize the text in 3 concise Korean sentences.
2. Extract 7-10 relevant keywords in Korean.

Provide the output in a JSON object with two keys: "summary" and "keywords".
Example: {{"summary": "...", "keywords": ["...", "..."]}}
"""

GEMINI_CONTENT_SCORE_PROMPT = """
Analyze the relevance of the following TEXT to the CRAWLING GOAL.
Provide a score from 0.0 (not relevant) to 1.0 (highly relevant).

CRAWLING GOAL: "{instruction_prompt}"

TEXT:
"{content}"

Your response MUST be only a single floating-point number (e.g., 0.85).
"""

# --- 로컬 LLM(Ollama)용 프롬프트 템플릿 ---
LOCAL_LINK_EVAL_PROMPT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an intelligent web crawler agent. Your task is to evaluate the relevance of a given link to a specific goal.
Respond with a single floating-point number between 0.0 and 1.0, where 1.0 is highly relevant.
Your response MUST be only the number. For example: 0.85<|eot_id|>
<|start_header_id|>user<|end_header_id|>
CRAWLING GOAL: "{target_goal}"
LINK DATA:
- Link Text: "{link_text}"
- URL: "{url}"
- Context: "{context}"
Based on the goal, what is the relevance score of this link?<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""

LOCAL_CONTENT_ENRICH_PROMPT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert text analyst. Your task is to summarize a given text and extract keywords.
Provide the output as a valid JSON object with two keys: "summary" (a 3-sentence summary in Korean) and "keywords" (a list of 7-10 Korean keywords).
Your response MUST be only the JSON object.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
Main Goal: "{instruction_prompt}"
Text to analyze:
"{content}"
Analyze the text and provide the JSON output.<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""

LOCAL_CONTENT_SCORE_PROMPT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an intelligent web crawler agent. Your task is to evaluate the relevance of a given TEXT to a specific goal.
Respond with a single floating-point number between 0.0 and 1.0, where 1.0 is highly relevant.
Your response MUST be only the number. For example: 0.85<|eot_id|>
<|start_header_id|>user<|end_header_id|>
CRAWLING GOAL: "{instruction_prompt}"
TEXT:
"{content}"
Based on the goal, what is the relevance score of this text?<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""

@dataclass
class CrawlerConfig:
    # --- 기본값이 없는 필드를 모두 위로 이동 ---
    routing_llm_provider: str
    analysis_llm_provider: str
    gemini_api_key: str
    routing_gemini_model: str
    analysis_local_model: str
    gemini_max_tokens: int
    crawler_engine: str
    max_pages_per_session: int
    relevance_threshold: float
    request_delay: float
    max_concurrent_requests: int
    user_agent: str
    page_load_timeout: int
    http_timeout: int

    # --- 기본값이 있는 필드(프롬프트)를 모두 아래로 이동 ---
    gemini_link_eval_prompt: str = field(default=GEMINI_LINK_EVAL_PROMPT, repr=False)
    gemini_content_enrich_prompt: str = field(default=GEMINI_CONTENT_ENRICH_PROMPT, repr=False)
    gemini_content_score_prompt: str = field(default=GEMINI_CONTENT_SCORE_PROMPT, repr=False)
    local_link_eval_prompt: str = field(default=LOCAL_LINK_EVAL_PROMPT, repr=False)
    local_content_enrich_prompt: str = field(default=LOCAL_CONTENT_ENRICH_PROMPT, repr=False)
    local_content_score_prompt: str = field(default=LOCAL_CONTENT_SCORE_PROMPT, repr=False)

    @classmethod
    def from_env(cls) -> 'CrawlerConfig':
        return cls(
            routing_llm_provider=os.getenv('ROUTING_LLM_PROVIDER', 'gemini').lower(),
            analysis_llm_provider=os.getenv('ANALYSIS_LLM_PROVIDER', 'local').lower(),
            gemini_api_key=os.getenv('GEMINI_API_KEY', ''),
            routing_gemini_model=os.getenv('ROUTING_GEMINI_MODEL', 'gemini-1.5-flash'),
            analysis_local_model=os.getenv('ANALYSIS_LOCAL_MODEL', 'llama3'),
            gemini_max_tokens=int(os.getenv('GEMINI_MAX_TOKENS', '1000')),
            crawler_engine=os.getenv('CRAWLER_ENGINE', 'aiohttp').lower(),
            max_pages_per_session=int(os.getenv('MAX_PAGES_PER_SESSION', '50')),
            relevance_threshold=float(os.getenv('RELEVANCE_THRESHOLD', '0.7')),
            request_delay=float(os.getenv('REQUEST_DELAY', '1.0')),
            max_concurrent_requests=int(os.getenv('MAX_CONCURRENT_REQUESTS', '5')),
            user_agent=os.getenv('USER_AGENT', 'LLM-Crawler-Agent/1.0'),
            page_load_timeout=int(os.getenv('PAGE_LOAD_TIMEOUT', '30')),
            http_timeout=int(os.getenv('HTTP_TIMEOUT', '15')),
        )

config = CrawlerConfig.from_env()
# config/settings.py

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

# --- Gemini용 프롬프트 템플릿 (일괄 처리용) ---
GEMINI_BATCH_LINK_EVAL_PROMPT = """
Analyze the relevance of the following JSON list of links to the CRAWLING GOAL.
For each link object, add a "score" key with a value from 0.0 to 1.0.

CRAWLING GOAL: "{target_goal}"

LINK LIST (JSON):
{links_json_str}

Your response MUST be only the JSON list, with the "score" key added to each object.
"""

GEMINI_COMBINED_ANALYSIS_PROMPT = """
Analyze the following text, keeping the main goal in mind: "{instruction_prompt}".

TEXT:
"{content}"

TASKS:
1. Summarize the text in 3 concise Korean sentences.
2. Extract 7-10 relevant keywords in Korean.
3. Score the relevance of the TEXT to the CRAWLING GOAL from 0.0 to 1.0.

Provide the output in a single JSON object with three keys: "summary", "keywords", and "relevance_score".
Example: {{"summary": "...", "keywords": ["...", "..."], "relevance_score": 0.95}}
"""

# --- 로컬 LLM(Ollama)용 프롬프트 템플릿 (일괄 처리용) ---
LOCAL_BATCH_LINK_EVAL_PROMPT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an intelligent web crawler agent. Your task is to evaluate a batch of links. For each JSON object in the user-provided list, add a "score" key with a relevance score from 0.0 to 1.0. Your response MUST be only the updated JSON list.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
CRAWLING GOAL: "{target_goal}"
LINK LIST (JSON):
{links_json_str}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

LOCAL_COMBINED_ANALYSIS_PROMPT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert text analyst. For the given text, perform three tasks: 1. Summarize it in 3 Korean sentences. 2. Extract 7-10 Korean keywords. 3. Score its relevance to the GOAL from 0.0 to 1.0.
Provide the output as a single valid JSON object with keys "summary", "keywords", and "relevance_score". Your response MUST be only the JSON object.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
GOAL: "{instruction_prompt}"
TEXT:
"{content}"
<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""


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
    gemini_batch_link_eval_prompt: str = field(default=GEMINI_BATCH_LINK_EVAL_PROMPT, repr=False)
    gemini_combined_analysis_prompt: str = field(default=GEMINI_COMBINED_ANALYSIS_PROMPT, repr=False)
    local_batch_link_eval_prompt: str = field(default=LOCAL_BATCH_LINK_EVAL_PROMPT, repr=False)
    local_combined_analysis_prompt: str = field(default=LOCAL_COMBINED_ANALYSIS_PROMPT, repr=False)
    # ---------------------------

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
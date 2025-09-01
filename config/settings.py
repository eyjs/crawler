import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

# --- Gemini용 프롬프트 ---
GEMINI_RELEVANCE_CHECK_PROMPT = """
Is the following TEXT directly related to the CRAWLING GOAL?
Answer with only a single word: "YES" or "NO".

CRAWLING GOAL: "{instruction_prompt}"
TEXT (first 500 characters): "{content}"
"""

GEMINI_COMBINED_ANALYSIS_PROMPT = """
Analyze the following text, keeping the main goal in mind: "{instruction_prompt}".
TEXT: "{content}"
TASKS: 1. Summarize the text in 3 concise Korean sentences. 2. Extract 7-10 relevant keywords in Korean. 3. Score the relevance of the TEXT to the CRAWLING GOAL from 0.0 to 1.0.
Provide the output in a single JSON object with three keys: "summary", "keywords", and "relevance_score".
Example: {{"summary": "...", "keywords": ["...", "..."], "relevance_score": 0.95}}
"""

# --- 로컬 LLM(Ollama)용 프롬프트 ---
LOCAL_RELEVANCE_CHECK_PROMPT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a relevance classifier. Is the provided TEXT relevant to the GOAL? Your response MUST be only a single word: "YES" or "NO".<|eot_id|>
<|start_header_id|>user<|end_header_id|>
GOAL: "{instruction_prompt}"
TEXT (first 500 characters): "{content}"
<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

LOCAL_COMBINED_ANALYSIS_PROMPT = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert text analyst. For the given text, perform three tasks: 1. Summarize it in 3 Korean sentences. 2. Extract 7-10 Korean keywords. 3. Score its relevance to the GOAL from 0.0 to 1.0. Provide the output as a single valid JSON object with keys "summary", "keywords", and "relevance_score". Your response MUST be only the JSON object.<|eot_id|>
<|start_header_id|>user<|end_header_id|>
GOAL: "{instruction_prompt}"
TEXT: "{content}"
<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""


@dataclass
class CrawlerConfig:
    llm_provider: str
    gemini_api_key: str
    gemini_model: str
    analysis_local_model: str
    gemini_max_tokens: int
    max_pages_per_session: int
    relevance_threshold: float
    request_delay: float

    gemini_relevance_check_prompt: str = field(default=GEMINI_RELEVANCE_CHECK_PROMPT, repr=False)
    gemini_combined_analysis_prompt: str = field(default=GEMINI_COMBINED_ANALYSIS_PROMPT, repr=False)
    local_relevance_check_prompt: str = field(default=LOCAL_RELEVANCE_CHECK_PROMPT, repr=False)
    local_combined_analysis_prompt: str = field(default=LOCAL_COMBINED_ANALYSIS_PROMPT, repr=False)

    @classmethod
    def from_env(cls) -> 'CrawlerConfig':
        return cls(
            llm_provider=os.getenv('LLM_PROVIDER', 'local').lower(),
            gemini_api_key=os.getenv('GEMINI_API_KEY', ''),
            gemini_model=os.getenv('GEMINI_MODEL', 'gemini-1.5-flash-latest'),
            analysis_local_model=os.getenv('ANALYSIS_LOCAL_MODEL', 'llama3'),
            gemini_max_tokens=int(os.getenv('GEMINI_MAX_TOKENS', '8192')),
            max_pages_per_session=int(os.getenv('MAX_PAGES_PER_SESSION', '50')),
            relevance_threshold=float(os.getenv('RELEVANCE_THRESHOLD', '0.6')),
            request_delay=float(os.getenv('REQUEST_DELAY', '1.0')),
        )

config = CrawlerConfig.from_env()

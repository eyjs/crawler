# src/config.py

import logging
import pandas as pd
from pathlib import Path
from urllib.parse import urlparse
from typing import List, Dict

# config/settings.py에서 전역 config 객체를 가져옵니다.
from config.settings import config

logger = logging.getLogger(__name__)

def create_site_identifier(url: str) -> str:
    """ URL에서 'kyobo_life'와 같은 고유한 사이트 식별자를 생성합니다. """
    try:
        netloc = urlparse(url).netloc
        parts = netloc.replace('www.', '').split('.')
        if len(parts) > 2 and parts[1] not in ['co', 'go', 'or']:
            identifier = f"{parts[1]}_{parts[0]}"
        else:
            identifier = parts[0]
        return identifier.replace('-', '_')
    except Exception:
        return f"site_{hash(url)}"

def load_configs_from_prompt_xlsx(file_path: str = "input/prompt.xlsx") -> List[Dict]:
    """ 지정된 Excel 파일 경로에서 크롤링할 사이트 목록과 설정을 불러옵니다. """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"설정 파일을 찾을 수 없습니다: {file_path}")
        return []
    try:
        df = pd.read_excel(path, engine='openpyxl')
        url_col = next((col for col in df.columns if '주소' in col), None)
        name_col = next((col for col in df.columns if '기관' in col or '회사' in col), None)
        prompt_col = next((col for col in df.columns if '내용' in col), None)

        if not all([url_col, name_col, prompt_col]):
            logger.error("Excel 파일에서 '웹사이트 주소', '기관/단체/회사', '주요 내용' 컬럼을 찾을 수 없습니다.")
            return []
        configs = []
        for _, row in df.iterrows():
            base_url = row[url_col]
            if isinstance(base_url, str) and base_url.startswith('http'):
                configs.append({
                    "site_identifier": create_site_identifier(base_url),
                    "site_name": row[name_col],
                    "base_url": base_url,
                    "instruction_prompt": row[prompt_col],
                    "max_pages_to_crawl": config.max_pages_per_session,
                    "crawl_delay": config.request_delay
                })
        logger.info(f"{len(configs)}개의 사이트 설정을 성공적으로 불러왔습니다: {file_path}")
        return configs
    except Exception as e:
        logger.error(f"설정 파일 처리 중 오류 발생: {e}", exc_info=True)
        return []
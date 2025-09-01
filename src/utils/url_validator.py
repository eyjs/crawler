# src/utils/url_validator.py

from urllib.parse import urlparse

def is_valid_url(url: str, base_netloc: str) -> bool:
    try:
        parsed_url = urlparse(url)
        if parsed_url.scheme not in ['http', 'https']: return False
        if parsed_url.netloc != base_netloc: return False
        # 첨부파일 확장자는 data_extractor에서 처리하므로 여기서 막지 않음
        if "#" in url or "javascript:void(0)" in url: return False
        return True
    except Exception:
        return False
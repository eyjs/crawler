# src/utils/link_filter.py

import re

# LLM 평가에서 제외할 링크 텍스트 키워드 (정규표현식)
# "로그인", "가입", "약관", "정책", "채용", "맵" 등의 단어가 포함된 경우
EXCLUDED_TEXT_PATTERNS = re.compile(
    r"로그인|가입|약관|정책|개인정보|이용안내|사이트맵|찾아오시는|채용|문의|고객센터|패밀리사이트",
    re.IGNORECASE
)

# LLM 평가에서 제외할 URL 경로 패턴
# /login, /member, /join, /policy, /recruit, /sitemap, /auth 등
EXCLUDED_URL_PATTERNS = re.compile(
    r"/login|/member|/join|/policy|/recruit|/sitemap|/auth|/cart|/order",
    re.IGNORECASE
)

# 파일 다운로드 링크로 추정되는 확장자
FILE_EXTENSIONS = re.compile(
    r"\.(pdf|hwp|zip|rar|exe|dmg|jpg|png|gif|mp4|mp3|doc|docx|xls|xlsx|ppt|pptx)$",
    re.IGNORECASE
)


def is_link_relevant_for_eval(link_text: str, url: str) -> bool:
    """
    주어진 링크가 LLM 평가를 수행할 가치가 있는지 사전에 필터링합니다.
    - True: 평가할 가치가 있음 (API 호출 대상)
    - False: 평가할 필요 없음 (API 호출 제외)
    """

    # 1. 링크 텍스트 필터링
    if EXCLUDED_TEXT_PATTERNS.search(link_text):
        return False

    # 2. URL 경로 필터링
    if EXCLUDED_URL_PATTERNS.search(url):
        return False

    # 3. 파일 확장자 필터링
    if FILE_EXTENSIONS.search(url):
        return False

    # 모든 필터를 통과하면 True 반환
    return True
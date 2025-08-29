# src/crawler/aio_extractor.py (콘텐츠 추출 로직이 강화된 최종 버전)

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from loguru import logger
from typing import Dict, List, Any

from config.settings import config

class AioExtractor:
    """aiohttp 기반의 순수 비동기 콘텐츠 추출기"""

    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.timeout = aiohttp.ClientTimeout(total=config.page_load_timeout, connect=config.http_timeout)
        self.headers = {'User-Agent': config.user_agent}

    async def fetch_page_content(self, session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
        """비동기식으로 페이지 콘텐츠를 가져옵니다."""
        await asyncio.sleep(self.delay)

        try:
            async with session.get(url, headers=self.headers, timeout=self.timeout) as response:
                if response.status != 200:
                    logger.warning(f"  -> HTTP {response.status} 수신: {url}")
                    return {'url': url, 'success': False, 'error': f'HTTP {response.status}'}

                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')

                # --- title 추출 로직 ---
                title = soup.find('title').get_text(strip=True) if soup.find('title') else "N/A"

                # --- 강화된 본문 추출 로직 ---
                cleaned_content = self._get_main_content_text(soup)

                links = self._extract_links(soup, url)

                return {
                    'url': url, 'success': True, 'title': title, 'content': cleaned_content,
                    'links': links, 'content_length': len(cleaned_content), 'links_count': len(links)
                }

        except Exception as e:
            logger.error(f"  -> ❌ 페이지 로드 실패: {url} | 오류: {e}")
            return {'url': url, 'success': False, 'error': str(e)}

    def _get_main_content_text(self, soup: BeautifulSoup) -> str:
        """
        HTML에서 네비게이션, 푸터 등 불필요한 부분을 제거하고 핵심 본문만 추출합니다.
        """
        # 1. 명백히 불필요한 태그 일괄 제거
        for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'aside', 'form', 'iframe']):
            tag.decompose()

        # 2. 주요 콘텐츠 컨테이너를 우선순위로 탐색
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find('div', id='content') or
            soup.find('div', class_='content') or
            soup.find('div', id='main-content') or
            soup.find('div', class_='post-body') or
            soup.body # 최후의 수단
        )

        if not main_content:
            return ""

        # 3. 선택된 영역 내에서 자잘한 노이즈 추가 제거
        for tag in main_content.find_all(['button', 'a'], class_=['btn', 'button']):
            tag.decompose() # 버튼 제거
        for tag in main_content.find_all(class_=['share-buttons', 'pagination', 'related-posts']):
            tag.decompose() # 공유 버튼, 페이지네이션 등 제거

        # 4. 최종 텍스트 추출 및 정제
        text = main_content.get_text(separator=' ', strip=True)
        # 여러 공백을 하나로 합치고, 불필요한 줄바꿈 제거
        import re
        text = re.sub(r'\s{2,}', ' ', text).strip()
        return text

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        # ... (기존과 동일, 변경 없음) ...
        links = []
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']; text = link_tag.get_text(strip=True)
            if not text or len(text) < 2: continue
            full_url = urljoin(base_url, href).split('#')[0]
            parsed = urlparse(full_url)
            if parsed.scheme not in ['http', 'https']: continue
            context = link_tag.parent.get_text(strip=True)[:100] if link_tag.parent else ""
            links.append({'url': full_url, 'text': text[:100], 'context': context})
        return links
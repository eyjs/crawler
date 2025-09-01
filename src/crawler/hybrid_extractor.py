# src/crawler/hybrid_extractor.py

"""
Requests 기반 비동기 스타일 크롤러
"""
import requests
import asyncio
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from loguru import logger
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

from config.settings import config # <-- 설정 임포트

class AsyncStyleContentExtractor:
    """requests를 사용하지만 비동기 스타일로 동작하는 크롤러"""

    def __init__(self, timeout: int = 30, delay: float = 1.0, max_workers: int = 5):
        self.timeout = timeout
        self.delay = delay
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.user_agent # <-- 설정 값으로 변경
        })
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        self.executor.shutdown(wait=True)
        self.session.close()

    def _fetch_sync(self, url: str) -> Dict[str, any]:
        """동기식 페이지 가져오기 (내부 메서드)"""
        # logger.info(f"🔍 페이지 요청: {url}") # Agent에서 로그를 남기므로 중복 로그 제거

        try:
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code != 200:
                logger.warning(f"    ㄴ HTTP {response.status_code}: {url}")
                return {
                    'url': url,
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'content': '',
                    'links': []
                }

            # 컨텐츠 정리
            cleaned_content = self._clean_html_content(response.text)

            # 링크 추출
            links = self._extract_links(response.text, url)

            # logger.success(f"✅ 페이지 로드 성공: {url} (컨텐츠 {len(cleaned_content)}자, 링크 {len(links)}개)")

            # 요청 간격 준수
            time.sleep(self.delay)

            return {
                'url': url,
                'success': True,
                'content': cleaned_content,
                'links': links,
                'content_length': len(cleaned_content),
                'links_count': len(links)
            }

        except requests.exceptions.Timeout:
            logger.error(f"    ㄴ ⏰ 타임아웃: {url}")
            return {
                'url': url,
                'success': False,
                'error': 'Timeout',
                'content': '',
                'links': []
            }
        except Exception as e:
            logger.error(f"    ㄴ ❌ 페이지 로드 실패 {url}: {e}")
            return {
                'url': url,
                'success': False,
                'error': str(e),
                'content': '',
                'links': []
            }

    async def fetch_page_content(self, url: str) -> Dict[str, any]:
        """비동기 스타일 페이지 컨텐츠 가져오기"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._fetch_sync, url)

    def _clean_html_content(self, html: str) -> str:
        """HTML에서 실제 텍스트 컨텐츠만 추출"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            for tag in soup(['script', 'style', 'nav', 'header', 'footer',
                           'aside', 'menu', 'advertisement', 'ads']):
                tag.decompose()

            main_content = (
                soup.find('main') or
                soup.find('article') or
                soup.find('div', class_=['content', 'main', 'body']) or
                soup.body or
                soup
            )

            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
                import re
                text = re.sub(r'\s+', ' ', text)
                return text

            return ""

        except Exception as e:
            logger.error(f"HTML 정리 실패: {e}")
            return ""

    def _extract_links(self, html: str, base_url: str) -> List[Dict[str, str]]:
        """페이지에서 링크 추출"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            links = []

            for link_tag in soup.find_all('a', href=True):
                href = link_tag['href']
                text = link_tag.get_text(strip=True)

                if not text or len(text) < 2:
                    continue

                full_url = urljoin(base_url, href)

                parsed = urlparse(full_url)
                if parsed.scheme not in ['http', 'https']:
                    continue

                # 프래그먼트 제거 (#section)
                full_url = full_url.split('#')[0]

                context = self._get_link_context(link_tag)

                links.append({
                    'url': full_url,
                    'text': text[:100],
                    'context': context
                })

            return links

        except Exception as e:
            logger.error(f"링크 추출 실패: {e}")
            return []

    def _get_link_context(self, link_tag, context_length: int = 100) -> str:
        """링크 주변 컨텍스트 추출"""
        try:
            parent = link_tag.parent
            if parent:
                context_text = parent.get_text(strip=True)
                return context_text[:context_length]
            return ""
        except:
            return ""
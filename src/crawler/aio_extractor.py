# src/crawler/aio_extractor.py

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from loguru import logger
from typing import Dict, List, Any, Optional
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import os
from datetime import datetime
import mimetypes
import uuid

from config.settings import config
from src.models.packet import AttachmentInfo

class AioExtractor:
    def __init__(self, delay: float = 1.0):
        self.delay = delay
        self.timeout = aiohttp.ClientTimeout(total=config.page_load_timeout, connect=config.http_timeout)
        self.headers = {'User-Agent': config.user_agent}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(5),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        before_sleep=lambda attempt: logger.warning(f"네트워크 오류, {attempt.attempt_number}/3번째 재시도 중...")
    )
    async def fetch_page_content(self, session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
        await asyncio.sleep(self.delay)
        try:
            async with session.get(url, headers=self.headers, timeout=self.timeout, allow_redirects=True) as response:
                response.raise_for_status()

                content_type = response.headers.get('Content-Type', '').lower()

                # HTML 페이지가 아닐 경우, 직접 파일로 다운로드
                if 'text/html' not in content_type:
                    logger.info(f"HTML이 아닌 콘텐츠 유형 감지 ({content_type}). 첨부파일로 직접 처리합니다.")
                    attachment_info = await self._download_binary_content(response, str(response.url))
                    return {
                        'url': str(response.url), 'success': True, 'title': os.path.basename(urlparse(str(response.url)).path),
                        'content': "", 'links': [], 'attachments': [attachment_info] if attachment_info else []
                    }

                # HTML 페이지일 경우, 텍스트 파싱 및 첨부파일 링크 탐색
                html = await response.text(errors='ignore')
                soup = BeautifulSoup(html, 'lxml')

                title = soup.find('title').get_text(strip=True) if soup.find('title') else "N/A"
                cleaned_content = self._get_main_content_text(soup)
                links = self._extract_links(soup, str(response.url))
                attachments = await self.download_attachments_from_links(session, soup, str(response.url))

                return {
                    'url': str(response.url), 'success': True, 'title': title, 'content': cleaned_content,
                    'links': links, 'attachments': attachments
                }
        except Exception as e:
            logger.error(f"  -> ❌ (최종 실패) 페이지 로드 실패: {url} | 오류: {e}")
            return {'url': url, 'success': False, 'error': str(e)}

    async def download_attachments_from_links(self, session: aiohttp.ClientSession, soup: BeautifulSoup, base_url: str) -> List[AttachmentInfo]:
        attachment_links = self._find_attachment_links(soup, base_url)
        if not attachment_links:
            return []

        date_str = datetime.now().strftime("%Y-%m-%d")
        domain = urlparse(base_url).netloc
        attachment_dir = os.path.join("output", date_str, domain, "attachments")
        os.makedirs(attachment_dir, exist_ok=True)

        download_tasks = [self._download_file(session, link_info, attachment_dir) for link_info in attachment_links]
        downloaded_files = await asyncio.gather(*download_tasks)

        return [info for info in downloaded_files if info]

    def _find_attachment_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        links = []
        file_extensions = ['.pdf', '.hwp', '.zip', '.rar', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.jpg', '.png']
        for tag in soup.find_all('a', href=True):
            href = tag.get('href', '').lower()
            if any(href.endswith(ext) for ext in file_extensions) or "download" in href or "file" in href:
                full_url = urljoin(base_url, tag.get('href'))
                file_name = os.path.basename(urlparse(full_url).path) or str(uuid.uuid4())
                links.append({"url": full_url, "name": file_name})
        return links

    async def _download_binary_content(self, response: aiohttp.ClientResponse, url: str) -> Optional[AttachmentInfo]:
        date_str = datetime.now().strftime("%Y-%m-%d")
        domain = urlparse(url).netloc
        attachment_dir = os.path.join("output", date_str, domain, "attachments")
        os.makedirs(attachment_dir, exist_ok=True)

        file_name = os.path.basename(urlparse(url).path) or str(uuid.uuid4())
        local_path = os.path.join(attachment_dir, file_name)

        try:
            with open(local_path, 'wb') as f:
                while True:
                    chunk = await response.content.read(8192)
                    if not chunk: break
                    f.write(chunk)

            file_type, _ = mimetypes.guess_type(local_path)
            relative_path = os.path.relpath(local_path, start="output").replace("\\", "/")
            logger.info(f"  -> 💾 직접 연결 파일 다운로드 성공: {relative_path}")
            return AttachmentInfo(file_name=file_name, original_url=url, local_path=relative_path, file_type=file_type or 'application/octet-stream')
        except Exception as e:
            logger.error(f"  -> ❌ 직접 연결 파일 다운로드 실패: {url} | 오류: {e}")
            return None

    async def _download_file(self, session: aiohttp.ClientSession, link_info: Dict[str, str], save_dir: str) -> Optional[AttachmentInfo]:
        url, file_name = link_info['url'], link_info['name']
        local_path = os.path.join(save_dir, file_name)

        try:
            async with session.get(url, timeout=self.timeout, allow_redirects=True) as response:
                response.raise_for_status()
                with open(local_path, 'wb') as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk: break
                        f.write(chunk)

                file_type, _ = mimetypes.guess_type(local_path)
                relative_path = os.path.relpath(local_path, start="output").replace("\\", "/")
                logger.info(f"  -> 💾 첨부파일 다운로드 성공: {relative_path}")
                return AttachmentInfo(file_name=file_name, original_url=url, local_path=relative_path, file_type=file_type or 'application/octet-stream')
        except Exception as e:
            logger.error(f"  -> ❌ 첨부파일 다운로드 실패: {url} | 오류: {e}")
            return None

    def _get_main_content_text(self, soup: BeautifulSoup) -> str:
        for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'aside', 'form', 'iframe']):
            tag.decompose()
        main_content = (soup.find('main') or soup.find('article') or soup.find('div', id='content') or soup.body)
        if not main_content: return ""
        for tag in main_content.find_all(class_=['share-buttons', 'pagination', 'related-posts', 'breadcrumbs']):
            tag.decompose()
        text = main_content.get_text(separator=' ', strip=True)
        import re
        text = re.sub(r'\s{2,}', ' ', text).strip()
        return text

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        links = []
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            text = link_tag.get_text(strip=True)
            if not text or len(text) < 2: continue
            full_url = urljoin(base_url, href).split('#')[0]
            if urlparse(full_url).scheme not in ['http', 'https']: continue
            context = link_tag.parent.get_text(strip=True)[:100] if link_tag.parent else ""
            links.append({'url': full_url, 'text': text[:100], 'context': context})
        return links
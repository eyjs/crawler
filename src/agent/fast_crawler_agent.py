# src/agent/fast_crawler_agent.py

import asyncio
import json
import logging
import time
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import Dict

from src.crawler.data_extractor_2 import DataExtractor
from src.utils.url_validator import is_valid_url
from src.feedback.knowledge_base import KnowledgeBase
from src.feedback.processed_ledger import ProcessedLedger

logger = logging.getLogger(__name__)

class FastCrawlerAgent:
    def __init__(self, config: Dict):
        self.config = config
        self.site_identifier = self.config["site_identifier"]
        self.base_url = self.config["base_url"]
        self.base_netloc = urlparse(self.base_url).netloc
        self.queue = deque([self.base_url])
        self.visited_urls = set([self.base_url])
        self.output_dir = Path("crawled_data") / self.site_identifier
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_base = KnowledgeBase(site_identifier=self.site_identifier)
        self.processed_ledger = ProcessedLedger(site_identifier=self.site_identifier)
        self.stats = {
            "pages_scanned": 0, "links_queued": 1, "links_ignored_by_kb": 0,
            "links_ignored_as_problematic": 0, "pages_skipped_as_unchanged": 0,
            "data_saved": 0, "start_time": time.time(),
        }
        logger.info(f"[{self.site_identifier}] FastCrawlerAgent 초기화 완료.")

    async def run(self):
        logger.info(f"[{self.site_identifier}] 고속 크롤링 시작. 목표: '{self.config['instruction_prompt']}'")
        max_pages = self.config.get("max_pages_to_crawl", 50)
        crawl_delay = self.config.get("crawl_delay", 1.0)
        extractor = DataExtractor()
        while self.queue and self.stats["pages_scanned"] < max_pages:
            current_url = self.queue.popleft()
            self.stats["pages_scanned"] += 1
            logger.info(f"[{self.site_identifier}] 처리 중 ({self.stats['pages_scanned']}/{max_pages}): {current_url}")
            try:
                page_data = await extractor.extract(current_url, self.base_url, self.site_identifier)
                if not page_data or not page_data.get('main_text'):
                    continue
                content_text = page_data['main_text']
                if not self.processed_ledger.has_changed(current_url, content_text):
                    self.stats["pages_skipped_as_unchanged"] += 1
                    logger.info(f"콘텐츠 변경 없음, 저장 건너뜀: {current_url}")
                else:
                    self._save_crawled_data(page_data)
                    self.stats["data_saved"] += 1
                self._enqueue_links(page_data.get('links', []))
                await asyncio.sleep(crawl_delay)
            except Exception as e:
                logger.error(f"'{current_url}' 처리 중 심각한 오류 발생: {e}", exc_info=True)
        await extractor.close_session()
        self.log_performance()
        logger.info(f"[{self.site_identifier}] 고속 크롤링 세션 종료.")

    def _enqueue_links(self, links: list[tuple[str, str]]):
        for url, _ in links:
            if is_valid_url(url, self.base_netloc) and url not in self.visited_urls:
                self.visited_urls.add(url)
                if self.knowledge_base.should_ignore(url):
                    self.stats["links_ignored_by_kb"] += 1
                    continue
                if self.knowledge_base.is_problematic(url):
                    self.stats["links_ignored_as_problematic"] += 1
                    logger.warning(f"🚫 파싱 실패 다수 발생, 위험 경로 회피: {url}")
                    continue
                self.queue.append(url)
                self.stats["links_queued"] += 1

    def _save_crawled_data(self, page_data: dict):
        file_id = f"{int(time.time() * 1000)}_{self.stats['data_saved']}.json"
        output_path = self.output_dir / file_id
        data_to_save = {
            "source_info": self.config,
            "crawled_content": {
                "url": page_data['url'], "title": page_data['title'],
                "extracted_text": page_data['main_text']
            }, "metadata": {"crawl_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        }
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"'{output_path}' 파일 저장 실패: {e}")

    def log_performance(self):
        elapsed_time = time.time() - self.stats["start_time"]
        pages_per_sec = self.stats["pages_scanned"] / elapsed_time if elapsed_time > 0 else 0
        summary = self.stats.copy()
        summary["total_duration_seconds"] = round(elapsed_time, 2)
        summary["pages_per_second"] = round(pages_per_sec, 2)
        logger.info(f"[{self.site_identifier}] 성능 요약: {json.dumps(summary, indent=2, ensure_ascii=False)}")
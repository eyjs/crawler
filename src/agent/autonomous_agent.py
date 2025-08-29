# src/agent/autonomous_agent.py

import asyncio
import aiohttp
from collections import deque
from urllib.parse import urlparse
from loguru import logger
from dataclasses import asdict
import json
import os

from src.crawler.aio_extractor import AioExtractor
from src.crawler.hybrid_extractor import AsyncStyleContentExtractor
from src.llm import routing_llm, analysis_llm
from config.settings import config
from src.utils.link_filter import is_link_relevant_for_eval
from src.models.packet import DataPacket, SourceInfo, CrawledContent, Metadata

class AutonomousAgent:
    def __init__(self, start_url: str, instruction_prompt: str, site_name: str = ""):
        self.start_url = start_url
        self.instruction_prompt = instruction_prompt
        self.base_domain = urlparse(start_url).netloc
        self.state_file_path = os.path.join("states", f"{self.base_domain}.json")
        self.strategy_file_path = os.path.join("states", f"{self.base_domain}_strategy.md")
        self.strategic_notes = ""

        self.source_info = SourceInfo(
            site_identifier=site_name or self.base_domain.replace('.', '_'),
            site_name=site_name or self.base_domain,
            base_url=self.start_url,
            instruction_prompt=self.instruction_prompt
        )

        self.to_visit_queue = deque([start_url])
        self.visited_urls = set([start_url])
        self.url_score_cache = {}
        self.crawled_data_packets = []

        logger.info(f"에이전트 초기화: {self.base_domain}")
        self.load_state()
        self.load_strategy()

    def load_state(self):
        os.makedirs("states", exist_ok=True)
        if os.path.exists(self.state_file_path):
            try:
                with open(self.state_file_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                loaded_queue = state.get('to_visit_queue', [])
                if not loaded_queue:
                    logger.info(f"이전 작업이 완료되어 '{self.base_domain}' 사이트를 새로 시작합니다.")
                    return
                self.to_visit_queue = deque(loaded_queue)
                self.visited_urls = set(state.get('visited_urls', {self.start_url}))
                self.url_score_cache = state.get('url_score_cache', {})
                logger.success(f"💾 상태 로드 완료. {len(self.to_visit_queue)}개의 URL을 이어서 크롤링합니다.")
            except Exception as e:
                logger.error(f"상태 파일 로드 실패: {e}. 처음부터 시작합니다.")

    def load_strategy(self):
        if os.path.exists(self.strategy_file_path):
            try:
                with open(self.strategy_file_path, 'r', encoding='utf-8') as f:
                    self.strategic_notes = f.read()
                if self.strategic_notes:
                    logger.info("📝 이전 크롤링에서 학습한 전략 노트를 불러왔습니다.")
            except Exception as e:
                logger.error(f"전략 노트 로드 실패: {e}")

    def save_state(self):
        state = {
            'to_visit_queue': list(self.to_visit_queue),
            'visited_urls': list(self.visited_urls),
            'url_score_cache': self.url_score_cache,
        }
        try:
            with open(self.state_file_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            logger.debug(f"상태 저장 완료: {self.state_file_path}")
        except Exception as e:
            logger.error(f"상태 파일 저장 실패: {e}")

    async def run(self):
        page_count = len(self.visited_urls)
        try:
            if config.crawler_engine == "aiohttp":
                await self.run_with_aiohttp(page_count)
            elif config.crawler_engine == "hybrid":
                await self.run_with_hybrid(page_count)
            else:
                logger.error(f"❌ 잘못된 크롤러 엔진 설정입니다: '{config.crawler_engine}'")
        finally:
            logger.info("최종 상태를 저장합니다...")
            self.save_state()

        logger.success(f"[{self.base_domain}] 크롤링 완료. 총 {len(self.crawled_data_packets)}개 데이터 패킷 생성.")
        return self.crawled_data_packets

    async def run_with_aiohttp(self, page_count: int):
        extractor = AioExtractor(delay=config.request_delay)
        async with aiohttp.ClientSession() as session:
            while self.to_visit_queue and page_count < config.max_pages_per_session:
                current_url = self.to_visit_queue.popleft()
                page_count += 1
                if page_count % 10 == 0:
                    self.save_state()
                await self.crawl_and_process_page(extractor, current_url, session=session)

    async def run_with_hybrid(self, page_count: int):
        async with AsyncStyleContentExtractor(
            timeout=config.page_load_timeout,
            delay=config.request_delay,
            max_workers=config.max_concurrent_requests
        ) as extractor:
            while self.to_visit_queue and page_count < config.max_pages_per_session:
                current_url = self.to_visit_queue.popleft()
                page_count += 1
                if page_count % 10 == 0:
                    self.save_state()
                await self.crawl_and_process_page(extractor, current_url)

    async def crawl_and_process_page(self, extractor, url: str, session=None):
        logger.info(f"[{len(self.visited_urls)}/{config.max_pages_per_session}] 크롤링 시도: {url}")
        page_data = await extractor.fetch_page_content(session, url) if session else await extractor.fetch_page_content(url)
        if not page_data or not page_data['success']:
            return

        if len(page_data.get('content', '')) < 300 and not page_data.get('attachments'):
            return

        await self.process_and_store_content(page_data, page_data.get('url', url))
        await self._evaluate_and_enqueue_links(page_data.get('links', []))

    async def process_and_store_content(self, page_data: dict, current_url: str):
        logger.info(f"  -> 유의미한 콘텐츠/첨부파일 발견. [분석 LLM]으로 후처리 시작...")
        analysis_input = page_data.get('content', '') or " ".join([att['file_name'] for att in page_data.get('attachments', [])])
        analysis_result = await analysis_llm.analyze_content(analysis_input, self.instruction_prompt)

        if not analysis_result or (not analysis_result.get('summary') and not page_data.get('attachments')):
            return

        crawled_content = CrawledContent(
            content_url=current_url,
            title=page_data.get('title', "N/A"),
            extracted_text=page_data.get('content', ''),
            summary=analysis_result.get('summary', ""),
            keywords=analysis_result.get('keywords', []),
            relevance_score=analysis_result.get('relevance_score', 0.0),
            attachments=page_data.get('attachments', [])
        )
        packet = DataPacket(
            source_info=self.source_info,
            crawled_content=crawled_content,
            metadata=Metadata(source_page_url=current_url)
        )
        self.crawled_data_packets.append(packet)
        logger.success(f"  -> ✅ 데이터 패킷 생성 성공 (Score: {crawled_content.relevance_score:.2f}): {packet.packet_id}")

    async def _evaluate_and_enqueue_links(self, links: list):
        valid_links_to_eval = [
            link for link in links
            if urlparse(link['url']).netloc == self.base_domain and
               link['url'] not in self.visited_urls and
               is_link_relevant_for_eval(link['text'], link['url'])
        ]

        if not valid_links_to_eval:
            return

        tasks = []
        for link in valid_links_to_eval:
            tasks.append(self.process_link(link))

        await asyncio.gather(*tasks)

    async def process_link(self, link: dict):
        url = link['url']
        if url in self.visited_urls: return

        # 캐시 확인
        if url in self.url_score_cache:
            score = self.url_score_cache[url]
            logger.debug(f"  -> 캐시 점수: {score:.2f} | {link['text'][:30]}...")
        else:
            logger.debug(f"  -> [라우팅 LLM] 링크 개별 평가 시작: {url}")
            score = await routing_llm.evaluate_relevance_score(
                link_text=link['text'],
                url=url,
                context=link['context'],
                target_goal=self.instruction_prompt,
                strategic_notes=self.strategic_notes
            )
            self.url_score_cache[url] = score
            logger.trace(f"  -> [라우팅 LLM] 평가 점수: {score:.2f} | {link.get('text', '')[:30]}...")

        if score >= config.relevance_threshold and url not in self.visited_urls:
            self.visited_urls.add(url)
            self.to_visit_queue.append(url)
            logger.info(f"  -> ⭐ 큐 추가 ({score:.2f}): {url}")
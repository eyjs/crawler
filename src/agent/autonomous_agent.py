# src/agent/autonomous_agent.py

import asyncio
import aiohttp
from collections import deque
from urllib.parse import urlparse
from loguru import logger
from dataclasses import asdict
import json

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

        self.source_info = SourceInfo(
            site_identifier=site_name or self.base_domain.replace('.', '_'),
            site_name=site_name or self.base_domain,
            base_url=self.start_url,
            instruction_prompt=self.instruction_prompt
        )
        self.to_visit_queue = deque([start_url])
        self.visited_urls = set([start_url])
        self.crawled_data_packets = []

        logger.info(f"에이전트 초기화: {self.base_domain}")
        logger.debug(f"설정된 목표: {self.instruction_prompt}")

    async def run(self):
        page_count = 0
        if config.crawler_engine == "aiohttp":
            logger.info("🚀 크롤링 엔진: aiohttp (고성능 비동기)")
            await self.run_with_aiohttp(page_count)
        elif config.crawler_engine == "hybrid":
            logger.info("🚀 크롤링 엔진: requests (안정적인 하이브리드)")
            await self.run_with_hybrid(page_count)
        else:
            logger.error(f"❌ 잘못된 크롤러 엔진 설정입니다: '{config.crawler_engine}'")

        logger.success(f"[{self.base_domain}] 크롤링 완료. 총 {len(self.crawled_data_packets)}개 데이터 패킷 생성.")
        return self.crawled_data_packets

    async def run_with_aiohttp(self, page_count: int):
        extractor = AioExtractor(delay=config.request_delay)
        async with aiohttp.ClientSession() as session:
            while self.to_visit_queue and page_count < config.max_pages_per_session:
                current_url = self.to_visit_queue.popleft()
                page_count += 1
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
                await self.crawl_and_process_page(extractor, current_url)

    async def crawl_and_process_page(self, extractor, url: str, session=None):
        logger.info(f"[{len(self.visited_urls)}/{config.max_pages_per_session}] 크롤링 시도: {url}")

        page_data = await extractor.fetch_page_content(session, url) if session else await extractor.fetch_page_content(url)

        if not page_data or not page_data['success'] or len(page_data.get('content', '')) < 300:
            logger.warning(f"페이지 로드 실패 또는 내용 없음: {url}")
            return

        await self.process_and_store_content(page_data, url)
        await self._evaluate_and_enqueue_links(page_data.get('links', []))

    async def process_and_store_content(self, page_data: dict, current_url: str):
        logger.info(f"  -> 유의미한 콘텐츠 발견. [분석 LLM]으로 통합 분석 시작...")
        content_text = page_data['content']

        analysis_result = await analysis_llm.analyze_content(content_text, self.instruction_prompt)

        if not analysis_result or not analysis_result.get('summary'):
            logger.warning("  -> 콘텐츠 강화 실패 (요약 내용 없음). 패킷을 생성하지 않습니다.")
            return

        crawled_content = CrawledContent(
            content_url=current_url,
            title=page_data.get('title', "N/A"),
            extracted_text=content_text,
            summary=analysis_result.get('summary', ""),
            keywords=analysis_result.get('keywords', []),
            relevance_score=analysis_result.get('relevance_score', 0.0)
        )
        packet = DataPacket(
            source_info=self.source_info,
            crawled_content=crawled_content,
            metadata=Metadata(source_page_url=current_url)
        )
        self.crawled_data_packets.append(packet)
        logger.success(f"  -> ✅ 데이터 패킷 생성 성공 (Score: {crawled_content.relevance_score:.2f}): {packet.packet_id}")

    async def _evaluate_and_enqueue_links(self, links: list):
        valid_links_to_eval = []
        for link in links:
            # url_score_cache에 없는 링크만 평가 대상으로 삼아 중복 평가 방지
            if urlparse(link['url']).netloc == self.base_domain and \
               link['url'] not in self.visited_urls and \
               is_link_relevant_for_eval(link['text'], link['url']):
                valid_links_to_eval.append(link)

        if not valid_links_to_eval:
            return

        logger.debug(f"  -> [라우팅 LLM] 링크 {len(valid_links_to_eval)}개 일괄 평가 시작...")
        scored_links = await routing_llm.evaluate_links_batch(valid_links_to_eval, self.instruction_prompt)

        for link in scored_links:
            url = link.get('url')
            score = link.get('score', 0.0)

            if not url: continue

            # 평가된 모든 링크의 점수를 캐시에 저장
            self.url_score_cache[url] = score
            logger.trace(f"  -> [라우팅 LLM] 평가 점수: {score:.2f} | {link.get('text', '')[:30]}...")

            if score >= config.relevance_threshold:
                if url not in self.visited_urls:
                    self.visited_urls.add(url)
                    self.to_visit_queue.append(url)
                    logger.info(f"  -> ⭐ 큐 추가 ({score:.2f}): {url}")
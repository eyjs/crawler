# src/agent/autonomous_agent.py (오류 수정 및 로그 레벨 조정된 최종 버전)

import asyncio
from collections import deque
from urllib.parse import urlparse
from loguru import logger
from dataclasses import asdict

from src.crawler.hybrid_extractor import AsyncStyleContentExtractor
from src.llm import llm_client
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
        self.url_score_cache = {}
        self.crawled_data_packets = []

        logger.info(f"에이전트 초기화: {self.base_domain}")
        logger.debug(f"설정된 목표: {self.instruction_prompt}")

    async def run(self):
        """에이전트 실행"""
        page_count = 0

        # --- 이 부분이 수정되었습니다 (Timeout 오류 해결) ---
        async with AsyncStyleContentExtractor(
            timeout=config.page_load_timeout,
            delay=config.request_delay,
            max_workers=config.max_concurrent_requests
        ) as extractor:
        # ------------------------------------------------
            while self.to_visit_queue and page_count < config.max_pages_per_session:
                current_url = self.to_visit_queue.popleft()
                page_count += 1

                logger.info(f"[{page_count}/{config.max_pages_per_session}] 크롤링 시도: {current_url}")

                page_data = await extractor.fetch_page_content(current_url)
                if not page_data or not page_data['success']:
                    logger.warning(f"페이지 로드 실패 또는 내용 없음: {current_url}")
                    continue

                if len(page_data.get('content', '')) < 300:
                    logger.debug(f"콘텐츠 길이 미달 (300자 미만), 건너뜀: {current_url}")
                    continue

                await self.process_and_store_content(page_data, current_url)
                await self._evaluate_and_enqueue_links(page_data.get('links', []))

        logger.success(f"[{self.base_domain}] 크롤링 완료. 총 {len(self.crawled_data_packets)}개 데이터 패킷 생성.")
        return self.crawled_data_packets

    async def process_and_store_content(self, page_data: dict, current_url: str):
        """콘텐츠를 강화하고 최종 데이터 패킷으로 저장합니다."""
        logger.info(f"  -> 유의미한 콘텐츠 발견. LLM으로 강화 시작...")

        content_text = page_data['content']
        enriched_data = await llm_client.enrich_content(content_text, self.instruction_prompt)

        if not enriched_data or not enriched_data['summary']:
            logger.warning("  -> 콘텐츠 강화 실패 (요약 내용 없음). 패킷을 생성하지 않습니다.")
            return

        crawled_content = CrawledContent(
            content_url=current_url,
            title=page_data.get('title', "N/A"),
            extracted_text=content_text,
            summary=enriched_data['summary'],
            keywords=enriched_data['keywords']
        )

        packet = DataPacket(
            source_info=self.source_info,
            crawled_content=crawled_content,
            metadata=Metadata(source_page_url=current_url)
        )

        self.crawled_data_packets.append(packet)
        logger.success(f"  -> ✅ 데이터 패킷 생성 성공: {packet.packet_id}")

    async def _evaluate_and_enqueue_links(self, links: list):
        """추출된 링크를 평가하고 큐에 추가합니다."""
        tasks = []
        for link in links:
            if urlparse(link['url']).netloc != self.base_domain: continue
            if link['url'] in self.visited_urls: continue
            if not is_link_relevant_for_eval(link['text'], link['url']):
                logger.trace(f"필터링됨 (API 호출 X): {link['text'][:30]}...")
                continue
            tasks.append(self.process_link(link))
        await asyncio.gather(*tasks)

    async def process_link(self, link: dict):
        """개별 링크를 처리하는 비동기 작업"""
        url = link['url']
        if url in self.visited_urls: return

        if url in self.url_score_cache:
            score = self.url_score_cache[url]
            logger.debug(f"  -> 캐시 점수: {score:.2f} | {link['text'][:30]}...")
        else:
            score = await llm_client.evaluate_relevance_score(
                link_text=link['text'],
                url=url,
                context=link['context'],
                target_goal=self.instruction_prompt
            )
            self.url_score_cache[url] = score
            logger.debug(f"  -> API 평가 점수: {score:.2f} | {link['text'][:30]}...")

        if score >= config.relevance_threshold:
            self.visited_urls.add(url)
            self.to_visit_queue.append(url)
            logger.info(f"  -> ⭐ 큐 추가 ({score:.2f}): {url}")
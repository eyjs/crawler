# src/agent/autonomous_agent.py (수정된 버전)

import asyncio
from collections import deque
from urllib.parse import urlparse
from loguru import logger
import json

from src.crawler.hybrid_extractor import AsyncStyleContentExtractor
from src.llm import llm_client
from config.settings import config
from src.utils.link_filter import is_link_relevant_for_eval
# --- 데이터 패킷 모델 임포트 ---
from src.models.packet import DataPacket, SourceInfo, CrawledContent, Metadata

class AutonomousAgent:
    def __init__(self, start_url: str, instruction_prompt: str, site_name: str = ""):
        self.start_url = start_url
        self.instruction_prompt = instruction_prompt
        self.base_domain = urlparse(start_url).netloc

        # --- 소스 정보 객체 생성 ---
        self.source_info = SourceInfo(
            site_identifier=site_name or self.base_domain.replace('.', '_'),
            site_name=site_name or self.base_domain,
            base_url=self.start_url,
            instruction_prompt=self.instruction_prompt
        )

        self.to_visit_queue = deque([start_url])
        self.visited_urls = set([start_url])
        self.url_score_cache = {}
        self.crawled_data_packets = [] # <-- 최종 데이터 패킷을 저장할 리스트

        logger.info(f"에이전트 초기화: {self.base_domain}")
        logger.info(f"설정된 목표: {self.instruction_prompt}")

    async def run(self):
        """에이전트 실행"""
        page_count = 0

        async with AsyncStyleContentExtractor(...) as extractor:
            while self.to_visit_queue and page_count < config.max_pages_per_session:
                current_url = self.to_visit_queue.popleft()
                page_count += 1

                logger.info(f"[{page_count}/{config.max_pages_per_session}] 크롤링 시도: {current_url}")

                page_data = await extractor.fetch_page_content(current_url)
                if not page_data or not page_data['success'] or len(page_data.get('content', '')) < 300:
                    continue

                # --- 콘텐츠 강화 및 패킷 생성 ---
                await self.process_and_store_content(page_data, current_url)
                # -----------------------------

                await self._evaluate_and_enqueue_links(page_data.get('links', []))

        logger.success(f"[{self.base_domain}] 크롤링 완료. 총 {len(self.crawled_data_packets)}개 데이터 패킷 생성.")
        return self.crawled_data_packets

    async def process_and_store_content(self, page_data: dict, current_url: str):
        """콘텐츠를 강화하고 최종 데이터 패킷으로 저장합니다."""
        logger.info(f"  -> 유의미한 콘텐츠 발견. LLM으로 강화 시작...")

        content_text = page_data['content']
        enriched_data = await llm_client.enrich_content(content_text, self.instruction_prompt)

        if not enriched_data or not enriched_data['summary']:
            logger.warning("  -> 콘텐츠 강화 실패. 요약이 비어있습니다.")
            return

        crawled_content = CrawledContent(
            content_url=current_url,
            title=page_data.get('title', current_url), # ToDo: title 추출 기능 추가 필요
            extracted_text=content_text,
            summary=enriched_data['summary'],
            keywords=enriched_data['keywords']
        )

        packet = DataPacket(
            source_info=self.source_info,
            crawled_content=crawled_content,
            metadata=Metadata(source_page_url=current_url) # ToDo: 더 정확한 source_page_url 필요
        )

        self.crawled_data_packets.append(packet)
        logger.success(f"  -> ✅ 데이터 패킷 생성 완료: {packet.packet_id}")

        # 임시로 파일에 저장하여 확인 (나중에 백엔드 전송 로직으로 대체)
        self.save_packet_to_file(packet)

    def save_packet_to_file(self, packet: DataPacket):
        """생성된 패킷을 JSON 파일로 저장 (테스트용)"""
        import os
        from dataclasses import asdict

        output_dir = "crawled_results"
        os.makedirs(output_dir, exist_ok=True)

        file_path = os.path.join(output_dir, f"{packet.packet_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(packet), f, ensure_ascii=False, indent=2)

    async def _evaluate_and_enqueue_links(self, links: list):
        # ... (기존 코드와 동일, 변경 없음)
        tasks = []
        for link in links:
            if urlparse(link['url']).netloc != self.base_domain: continue
            if link['url'] in self.visited_urls: continue
            if not is_link_relevant_for_eval(link['text'], link['url']): continue
            tasks.append(self.process_link(link))
        await asyncio.gather(*tasks)

    async def process_link(self, link: dict):
        # ... (기존 코드와 동일, 변경 없음)
        url = link['url']
        if url in self.visited_urls: return
        if url in self.url_score_cache:
            score = self.url_score_cache[url]
        else:
            score = await llm_client.evaluate_relevance_score(...)
            self.url_score_cache[url] = score
        if score >= config.relevance_threshold:
            self.visited_urls.add(url)
            self.to_visit_queue.append(url)
            logger.info(f"  -> ⭐ 큐 추가 ({score:.2f}): {url}")
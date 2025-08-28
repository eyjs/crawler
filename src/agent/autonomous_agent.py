# src/agent/autonomous_agent.py

import asyncio
from collections import deque
from urllib.parse import urlparse
from loguru import logger

from src.crawler.hybrid_extractor import AsyncStyleContentExtractor
from src.llm.gemini_client import gemini_client
from config.settings import config

class AutonomousAgent:
    def __init__(self, start_url: str, instruction_prompt: str):
        self.start_url = start_url
        self.instruction_prompt = instruction_prompt
        self.base_domain = urlparse(start_url).netloc

        # 크롤링 상태 관리
        self.to_visit_queue = deque([start_url])
        self.visited_urls = set([start_url])

        # 수집된 결과
        self.crawled_data = []

        logger.info(f"🚀 에이전트 초기화: {self.base_domain}")
        logger.info(f"🎯 목표: {self.instruction_prompt}")

    async def run(self):
        """에이전트 실행"""
        page_count = 0

        async with AsyncStyleContentExtractor(
            timeout=config.page_load_timeout,
            delay=config.request_delay,
            max_workers=config.max_concurrent_requests
        ) as extractor:

            while self.to_visit_queue and page_count < config.max_pages_per_session:
                current_url = self.to_visit_queue.popleft()
                page_count += 1

                logger.info(f"[{page_count}/{config.max_pages_per_session}] ➡️  페이지 크롤링: {current_url}")

                # 1. 페이지 콘텐츠 및 링크 추출
                page_data = await extractor.fetch_page_content(current_url)
                if not page_data or not page_data['success']:
                    continue

                # (향후) 추출된 콘텐츠 처리 로직 (여기서 패킷 생성 및 전송)
                if len(page_data.get('content', '')) > 300: # 최소 콘텐츠 길이 검증
                    self.crawled_data.append({
                        "url": current_url,
                        "content": page_data['content']
                    })
                    logger.info(f"    ㄴ 유의미한 콘텐츠 발견 (길이: {len(page_data['content'])})")


                # 2. 링크 관련성 평가 및 큐에 추가
                await self._evaluate_and_enqueue_links(page_data.get('links', []))

        logger.success(f"✅ [{self.base_domain}] 크롤링 완료. 총 {len(self.crawled_data)}개 유의미한 페이지 수집.")
        return self.crawled_data

    async def _evaluate_and_enqueue_links(self, links: list):
        """추출된 링크를 평가하고 큐에 추가합니다."""
        tasks = []
        for link in links:
            # 같은 도메인의 링크만 평가 대상으로 한정
            if urlparse(link['url']).netloc != self.base_domain:
                continue

            # 이미 방문했거나 큐에 있는 링크는 건너뜀
            if link['url'] in self.visited_urls:
                continue

            tasks.append(self._process_link(link))

        await asyncio.gather(*tasks)

    async def _process_link(self, link: dict):
        """개별 링크를 처리하는 비동기 작업"""
        url = link['url']

        # 중복 추가 방지
        if url in self.visited_urls:
            return

        score = await gemini_client.evaluate_relevance_score(
            link_text=link['text'],
            url=url,
            context=link['context'],
            target_goal=self.instruction_prompt
        )

        logger.debug(f"평가: {score:.2f} | {link['text'][:30]}... | {url}")

        if score >= config.relevance_threshold:
            # 방문 목록에 먼저 추가하여 중복 작업 방지
            self.visited_urls.add(url)
            self.to_visit_queue.append(url)
            logger.success(f"⭐ 관련성 높은 링크({score:.2f}) 발견 -> 큐 추가: {url}")
# src/crawler/high_performance_extractor.py

import logging
import asyncio
import aiohttp
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from lxml import html, etree
from lxml.html.clean import Cleaner
from urllib.parse import urljoin, urlparse, parse_qs, unquote
from pathlib import Path
import io
import json
import time
import re
import hashlib
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass

# 문서 처리 라이브러리
from pypdf import PdfReader
from docx import Document
import pandas as pd
from pptx import Presentation

logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    """추출 결과를 담는 데이터 클래스"""
    url: str
    title: str
    main_text: str
    links: List[Tuple[str, str]]
    processing_time: float
    quality_score: float

@dataclass
class BatchExtractionConfig:
    """배치 처리 설정"""
    batch_size: int = 50
    max_workers: int = None
    chunk_size: int = 10
    timeout: int = 30

class HighPerformanceExtractor:
    """
    [v3.0] 고성능 멀티프로세싱 + lxml 파서를 활용한 대규모 크롤링 전용 추출기
    
    주요 개선사항:
    - lxml 파서: BeautifulSoup 대비 5-10배 빠른 HTML 파싱
    - 멀티프로세싱: CPU 집약적 작업을 병렬로 처리
    - 배치 처리: 네트워크 요청을 효율적으로 묶어서 처리
    - 메모리 최적화: 대용량 데이터 스트리밍 처리
    """
    
    def __init__(self, config: BatchExtractionConfig = None):
        self.config = config or BatchExtractionConfig()
        
        # CPU 코어 수에 따른 워커 수 자동 조정
        if self.config.max_workers is None:
            self.config.max_workers = min(mp.cpu_count(), 16)
            
        # aiohttp 세션 설정 (고성능)
        connector = aiohttp.TCPConnector(
            limit=100,  # 전체 연결 풀 크기
            limit_per_host=20,  # 호스트별 최대 연결 수
            ttl_dns_cache=300,  # DNS 캐시 TTL
            use_dns_cache=True,
            keepalive_timeout=60,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(
            total=self.config.timeout,
            connect=10,
            sock_read=20
        )
        
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        # lxml Cleaner 설정 (보안 및 노이즈 제거)
        self.cleaner = Cleaner(
            scripts=True,
            style=True,
            meta=True,
            page_structure=False,
            embedded=True,
            frames=True,
            forms=True,
            remove_unknown_tags=False,
            safe_attrs_only=False,
            add_nofollow=True
        )
        
        # 멀티프로세스 처리를 위한 실행기
        self.process_executor = ProcessPoolExecutor(max_workers=self.config.max_workers)
        self.thread_executor = ThreadPoolExecutor(max_workers=self.config.max_workers * 2)
        
        # 성능 통계
        self.stats = {
            'total_processed': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'parse_time': 0.0,
            'network_time': 0.0
        }
        
        logger.info(f"고성능 추출기 초기화 완료 - 워커: {self.config.max_workers}, 배치: {self.config.batch_size}")

    async def extract_batch(self, urls: List[str], base_url: str, site_identifier: str) -> List[Optional[ExtractionResult]]:
        """
        URL 리스트를 배치로 처리하는 메인 메서드
        2000페이지도 효율적으로 처리 가능
        """
        start_time = time.time()
        
        # URL을 청크 단위로 분할
        url_chunks = [urls[i:i + self.config.chunk_size] 
                     for i in range(0, len(urls), self.config.chunk_size)]
        
        logger.info(f"[{site_identifier}] 배치 처리 시작: {len(urls)}개 URL, {len(url_chunks)}개 청크")
        
        # 청크별 병렬 처리
        tasks = []
        for chunk_idx, url_chunk in enumerate(url_chunks):
            task = self._process_chunk(url_chunk, base_url, site_identifier, chunk_idx)
            tasks.append(task)
        
        # 모든 청크 결과 수집
        chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 플래튼화
        results = []
        for chunk_result in chunk_results:
            if isinstance(chunk_result, Exception):
                logger.error(f"청크 처리 실패: {chunk_result}")
                continue
            results.extend(chunk_result)
        
        # 성능 통계 업데이트
        total_time = time.time() - start_time
        self.stats['total_processed'] += len(urls)
        self.stats['total_time'] += total_time
        
        avg_time = total_time / len(urls) if urls else 0
        throughput = len(urls) / total_time if total_time > 0 else 0
        
        logger.info(f"[{site_identifier}] 배치 처리 완료: {len(results)}/{len(urls)} 성공, "
                   f"평균 {avg_time:.3f}초/페이지, 처리량: {throughput:.1f}페이지/초")
        
        return results

    async def _process_chunk(self, urls: List[str], base_url: str, 
                           site_identifier: str, chunk_idx: int) -> List[Optional[ExtractionResult]]:
        """청크 단위 병렬 처리"""
        logger.info(f"[{site_identifier}] 청크 #{chunk_idx} 처리 시작: {len(urls)}개 URL")
        
        # 네트워크 요청을 먼저 병렬로 수행
        html_contents = await self._fetch_html_batch(urls)
        
        # HTML 파싱은 프로세스 풀에서 병렬 처리
        parse_tasks = []
        for url, html_content in zip(urls, html_contents):
            if html_content is None:
                parse_tasks.append(None)
                continue
                
            # CPU 집약적인 파싱 작업을 별도 프로세스에서 실행
            task = asyncio.get_event_loop().run_in_executor(
                self.process_executor,
                process_html_content,  # 순수 함수로 정의 (pickle 가능)
                html_content, url, base_url
            )
            parse_tasks.append(task)
        
        # 파싱 결과 수집
        parse_results = []
        for task in parse_tasks:
            if task is None:
                parse_results.append(None)
            else:
                try:
                    result = await task
                    parse_results.append(result)
                except Exception as e:
                    logger.error(f"파싱 실패: {e}")
                    parse_results.append(None)
        
        logger.info(f"[{site_identifier}] 청크 #{chunk_idx} 완료: "
                   f"{sum(1 for r in parse_results if r is not None)}/{len(urls)} 성공")
        
        return parse_results

    async def _fetch_html_batch(self, urls: List[str]) -> List[Optional[str]]:
        """배치 HTTP 요청 처리"""
        start_time = time.time()
        
        async def fetch_single(url: str) -> Optional[str]:
            try:
                async with self._session.get(url) as response:
                    if response.status != 200:
                        return None
                    
                    content_type = response.headers.get('Content-Type', '')
                    if 'text/html' not in content_type:
                        return None
                    
                    html = await response.text(encoding='utf-8', errors='ignore')
                    return html
                    
            except Exception as e:
                logger.debug(f"HTTP 요청 실패 {url}: {e}")
                return None
        
        # 세마포어로 동시 요청 수 제한
        semaphore = asyncio.Semaphore(20)  # 최대 20개 동시 요청
        
        async def controlled_fetch(url):
            async with semaphore:
                return await fetch_single(url)
        
        # 모든 URL을 병렬로 요청
        tasks = [controlled_fetch(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 예외를 None으로 변환
        html_contents = []
        for result in results:
            if isinstance(result, Exception):
                html_contents.append(None)
            else:
                html_contents.append(result)
        
        network_time = time.time() - start_time
        self.stats['network_time'] += network_time
        
        success_count = sum(1 for content in html_contents if content is not None)
        logger.debug(f"HTTP 배치 완료: {success_count}/{len(urls)} 성공, {network_time:.2f}초")
        
        return html_contents

    async def close(self):
        """리소스 정리"""
        await self._session.close()
        self.process_executor.shutdown(wait=True)
        self.thread_executor.shutdown(wait=True)
        
        logger.info(f"추출기 종료 - 총 처리: {self.stats['total_processed']}페이지, "
                   f"평균 처리 시간: {self.stats['total_time'] / max(1, self.stats['total_processed']):.3f}초")

# ==========================================
# 멀티프로세싱용 순수 함수들 (pickle 가능)
# ==========================================

def process_html_content(html_content: str, url: str, base_url: str) -> Optional[ExtractionResult]:
    """
    HTML 콘텐츠를 파싱하여 결과를 반환하는 순수 함수
    멀티프로세싱에서 사용 가능하도록 pickle 가능한 형태로 구현
    """
    try:
        start_time = time.time()
        
        # lxml을 사용한 빠른 HTML 파싱
        doc = html.fromstring(html_content)
        
        # 1단계: lxml Cleaner로 노이즈 제거 (매우 빠름)
        cleaner = Cleaner(
            scripts=True, style=True, meta=True, 
            embedded=True, frames=True, forms=True
        )
        clean_doc = cleaner.clean_html(doc)
        
        # 2단계: XPath를 사용한 빠른 제목 추출
        title_elements = clean_doc.xpath('//title/text()')
        title = title_elements[0].strip() if title_elements else url
        
        # 3단계: 본문 영역 식별 (lxml XPath 사용)
        main_text = extract_main_content_lxml(clean_doc)
        
        # 4단계: 링크 추출 (XPath 사용)
        links = extract_links_lxml(clean_doc, url, base_url)
        
        # 품질 점수 계산
        quality_score = calculate_content_quality(main_text)
        
        processing_time = time.time() - start_time
        
        return ExtractionResult(
            url=url,
            title=title,
            main_text=main_text,
            links=links,
            processing_time=processing_time,
            quality_score=quality_score
        )
        
    except Exception as e:
        # 로깅은 멀티프로세스 환경에서 복잡하므로 예외만 반환
        return None

def extract_main_content_lxml(doc) -> str:
    """lxml을 사용한 고속 본문 추출"""
    
    # 우선 순위별 본문 영역 셀렉터
    content_selectors = [
        "//main",
        "//article",
        "//*[@id='content']",
        "//*[@id='main']",
        "//*[@class='content']",
        "//*[@class='article']",
        "//*[@class='post']",
        "//div[contains(@class, 'content')]",
        "//div[contains(@class, 'article')]",
        "//div[contains(@class, 'post')]",
        "//body"
    ]
    
    # 최적의 본문 영역 찾기
    best_content = ""
    max_score = 0
    
    for selector in content_selectors:
        elements = doc.xpath(selector)
        for element in elements:
            # 노이즈 요소 제거
            for noise in element.xpath(".//script | .//style | .//nav | .//footer | .//header"):
                noise.getparent().remove(noise)
            
            text = element.text_content()
            if not text:
                continue
                
            score = len(text.strip())
            if score > max_score:
                max_score = score
                best_content = text
    
    # 텍스트 정제
    return clean_extracted_text(best_content)

def extract_links_lxml(doc, current_url: str, base_url: str) -> List[Tuple[str, str]]:
    """lxml XPath를 사용한 고속 링크 추출"""
    links = []
    base_netloc = urlparse(base_url).netloc
    
    # 모든 링크 요소를 한 번에 가져오기
    link_elements = doc.xpath("//a[@href]")
    
    for element in link_elements:
        href = element.get('href')
        if not href or href.startswith('#') or href.startswith('javascript:'):
            continue
            
        # 절대 URL로 변환
        absolute_url = urljoin(current_url, href)
        parsed = urlparse(absolute_url)
        
        # 같은 도메인만 수집
        if parsed.netloc != base_netloc:
            continue
            
        link_text = element.text_content().strip()
        if link_text:
            links.append((absolute_url, link_text))
    
    return links

def clean_extracted_text(text: str) -> str:
    """텍스트 정제 (공백, 개행 정리)"""
    if not text:
        return ""
    
    # 연속된 공백과 개행 정리
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # 불필요한 텍스트 패턴 제거
    noise_patterns = [
        r'다운로드|뷰어|첨부파일|목록으로|이전글|다음글|맨위로',
        r'Copyright.*All rights reserved',
        r'찾아오시는 길|개인정보처리방침',
        r'작성자\s*[:：]\s*\S+',
        r'등록일\s*[:：]\s*\d{4}[-/.]\d{1,2}[-/.]\d{1,2}',
        r'조회수\s*[:：]\s*\d+',
    ]
    
    for pattern in noise_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # 최종 정리
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if len(line) >= 10:  # 너무 짧은 줄 제외
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def calculate_content_quality(text: str) -> float:
    """콘텐츠 품질 점수 계산 (0-1)"""
    if not text:
        return 0.0
    
    score = 0.0
    text_len = len(text.strip())
    
    # 기본 길이 점수
    if text_len > 1000:
        score += 0.4
    elif text_len > 500:
        score += 0.3
    elif text_len > 100:
        score += 0.2
    
    # 문장 구조 점수
    sentence_count = len([s for s in text.split('.') if len(s.strip()) > 10])
    if sentence_count >= 5:
        score += 0.3
    elif sentence_count >= 2:
        score += 0.2
    
    # 정보성 키워드 점수
    info_keywords = ['설명', '내용', '정보', '소개', '개요', '현황', '실적', '계획', '전략']
    keyword_count = sum(1 for keyword in info_keywords if keyword in text)
    if keyword_count >= 3:
        score += 0.2
    elif keyword_count >= 1:
        score += 0.1
    
    # 중복 텍스트 패널티
    unique_lines = set(text.split('\n'))
    total_lines = len(text.split('\n'))
    if total_lines > 0:
        uniqueness = len(unique_lines) / total_lines
        score *= uniqueness
    
    return min(1.0, score)

# ==========================================
# 기존 인터페이스 호환 래퍼
# ==========================================

class FastDataExtractor:
    """
    기존 DataExtractor와 호환되는 인터페이스를 제공하는 래퍼 클래스
    기존 코드 수정 없이 고성능 버전 사용 가능
    """
    
    def __init__(self):
        self.hp_extractor = HighPerformanceExtractor(
            BatchExtractionConfig(
                batch_size=100,  # 대용량 배치
                max_workers=mp.cpu_count()
            )
        )
        self._batch_buffer = []
        self._batch_callbacks = []
    
    async def extract(self, url: str, base_url: str, site_identifier: str) -> Optional[Dict]:
        """단일 URL 처리 (기존 인터페이스 호환)"""
        results = await self.hp_extractor.extract_batch([url], base_url, site_identifier)
        
        if not results or results[0] is None:
            return None
            
        result = results[0]
        
        # 기존 형식으로 변환
        return {
            "url": result.url,
            "title": result.title,
            "main_text": result.main_text,
            "links": result.links
        }
    
    async def extract_batch_optimized(self, urls: List[str], base_url: str, 
                                    site_identifier: str) -> List[Optional[Dict]]:
        """배치 처리 최적화 메서드 (신규)"""
        results = await self.hp_extractor.extract_batch(urls, base_url, site_identifier)
        
        # 기존 형식으로 변환
        converted_results = []
        for result in results:
            if result is None:
                converted_results.append(None)
            else:
                converted_results.append({
                    "url": result.url,
                    "title": result.title,
                    "main_text": result.main_text,
                    "links": result.links
                })
        
        return converted_results
    
    async def close_session(self):
        """리소스 정리"""
        await self.hp_extractor.close()

# ==========================================
# 사용 예시
# ==========================================

async def demo_high_performance_crawling():
    """2000페이지 크롤링 데모"""
    
    # 2000개의 테스트 URL (실제로는 Excel에서 로드)
    test_urls = [f"https://example.com/page/{i}" for i in range(2000)]
    
    # 고성능 추출기 초기화
    config = BatchExtractionConfig(
        batch_size=200,  # 한 번에 200페이지씩 처리
        max_workers=8,   # 8개 프로세스 병렬 처리
        chunk_size=50    # 50페이지씩 청크 분할
    )
    
    extractor = HighPerformanceExtractor(config)
    
    try:
        start_time = time.time()
        logger.info("2000페이지 고성능 크롤링 시작...")
        
        results = await extractor.extract_batch(
            test_urls, 
            "https://example.com", 
            "performance_test"
        )
        
        end_time = time.time()
        success_count = sum(1 for r in results if r is not None)
        
        logger.info(f"크롤링 완료!")
        logger.info(f"총 처리 시간: {end_time - start_time:.2f}초")
        logger.info(f"성공률: {success_count}/{len(test_urls)} ({success_count/len(test_urls)*100:.1f}%)")
        logger.info(f"처리 속도: {len(test_urls)/(end_time - start_time):.1f} 페이지/초")
        
    finally:
        await extractor.close()

if __name__ == "__main__":
    # 성능 테스트 실행
    asyncio.run(demo_high_performance_crawling())

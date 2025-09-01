# src/agent/high_performance_crawler_agent.py

import asyncio
import json
import logging
import time
import multiprocessing as mp
from collections import deque
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, List, Set
from dataclasses import dataclass, asdict

from src.crawler.high_performance_extractor import FastDataExtractor, BatchExtractionConfig
from src.utils.url_validator import is_valid_url
from src.feedback.knowledge_base import KnowledgeBase
from src.feedback.processed_ledger import ProcessedLedger

logger = logging.getLogger(__name__)

@dataclass
class CrawlingStats:
    """크롤링 통계를 담는 데이터 클래스"""
    pages_discovered: int = 0
    pages_processed: int = 0
    pages_succeeded: int = 0
    pages_failed: int = 0
    pages_skipped_unchanged: int = 0
    pages_skipped_by_kb: int = 0
    pages_skipped_problematic: int = 0
    total_links_found: int = 0
    processing_time: float = 0.0
    avg_speed: float = 0.0
    
    def success_rate(self) -> float:
        return (self.pages_succeeded / max(1, self.pages_processed)) * 100
    
    def to_dict(self) -> dict:
        return asdict(self)

class HighPerformanceCrawlerAgent:
    """
    [v3.0] 대규모 크롤링을 위한 고성능 에이전트
    
    주요 특징:
    - 2000페이지 이상 처리 가능
    - 멀티프로세싱 + 배치 처리
    - 지능형 큐 관리
    - 실시간 성능 모니터링
    - 메모리 효율적 처리
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.site_identifier = self.config["site_identifier"]
        self.base_url = self.config["base_url"]
        self.base_netloc = urlparse(self.base_url).netloc
        
        # 큐와 집합을 효율적으로 관리
        self.pending_urls = deque([self.base_url])
        self.visited_urls: Set[str] = {self.base_url}
        self.failed_urls: Set[str] = set()
        
        # 디렉토리 설정
        self.output_dir = Path("crawled_data") / self.site_identifier
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 지식 베이스와 처리 기록
        self.knowledge_base = KnowledgeBase(site_identifier=self.site_identifier)
        self.processed_ledger = ProcessedLedger(site_identifier=self.site_identifier)
        
        # 통계 추적
        self.stats = CrawlingStats()
        
        # 고성능 추출기 설정
        max_pages = self.config.get("max_pages_to_crawl", 2000)
        cpu_count = mp.cpu_count()
        
        extractor_config = BatchExtractionConfig(
            batch_size=min(100, max_pages // 10),  # 전체의 10% 또는 최대 100
            max_workers=min(cpu_count, 12),        # CPU 코어 수 또는 최대 12
            chunk_size=20,                         # 청크 크기
            timeout=30                             # 타임아웃
        )
        
        self.extractor = FastDataExtractor()
        self.extractor.hp_extractor.config = extractor_config
        
        logger.info(f"[{self.site_identifier}] 고성능 크롤러 에이전트 초기화 완료")
        logger.info(f"최대 페이지: {max_pages}, 워커: {extractor_config.max_workers}, "
                   f"배치 크기: {extractor_config.batch_size}")

    async def run(self):
        """메인 크롤링 루프 - 대규모 처리 최적화"""
        logger.info(f"[{self.site_identifier}] 고성능 크롤링 시작")
        logger.info(f"목표: '{self.config['instruction_prompt']}'")
        
        start_time = time.time()
        max_pages = self.config.get("max_pages_to_crawl", 2000)
        crawl_delay = self.config.get("crawl_delay", 0.5)  # 고속 처리를 위해 단축
        
        try:
            while self.pending_urls and self.stats.pages_processed < max_pages:
                # 배치 크기만큼 URL 수집
                current_batch = self._collect_batch_urls()
                if not current_batch:
                    logger.info("더 이상 처리할 URL이 없습니다.")
                    break
                
                logger.info(f"[{self.site_identifier}] 배치 처리 중: "
                           f"{len(current_batch)}개 URL ({self.stats.pages_processed + 1}-"
                           f"{self.stats.pages_processed + len(current_batch)})")
                
                # 배치 처리 실행
                batch_results = await self._process_batch(current_batch)
                
                # 결과 처리 및 새 링크 수집
                await self._process_batch_results(batch_results)
                
                # 진행 상황 로깅
                self._log_progress()
                
                # 적응형 지연 시간 (부하 조절)
                if crawl_delay > 0:
                    await asyncio.sleep(crawl_delay * len(current_batch) / 10)
                
        except Exception as e:
            logger.error(f"[{self.site_identifier}] 크롤링 중 심각한 오류: {e}", exc_info=True)
        
        finally:
            # 리소스 정리
            await self.extractor.close_session()
            
            # 최종 통계
            self.stats.processing_time = time.time() - start_time
            if self.stats.processing_time > 0:
                self.stats.avg_speed = self.stats.pages_processed / self.stats.processing_time
            
            self._log_final_statistics()
            
        logger.info(f"[{self.site_identifier}] 고성능 크롤링 완료")

    def _collect_batch_urls(self) -> List[str]:
        """배치 처리를 위한 URL 수집"""
        batch_size = self.extractor.hp_extractor.config.batch_size
        current_batch = []
        
        # 큐에서 배치 크기만큼 URL 수집
        while len(current_batch) < batch_size and self.pending_urls:
            url = self.pending_urls.popleft()
            
            # 지식 베이스 기반 사전 필터링
            if self.knowledge_base.should_ignore(url):
                self.stats.pages_skipped_by_kb += 1
                continue
                
            if self.knowledge_base.is_problematic(url):
                self.stats.pages_skipped_problematic += 1
                continue
            
            current_batch.append(url)
        
        return current_batch

    async def _process_batch(self, urls: List[str]) -> List[Dict]:
        """URL 배치를 병렬 처리"""
        batch_start_time = time.time()
        
        # 고성능 배치 추출 실행
        results = await self.extractor.extract_batch_optimized(
            urls, self.base_url, self.site_identifier
        )
        
        # 통계 업데이트
        self.stats.pages_processed += len(urls)
        successful_results = [r for r in results if r is not None]
        self.stats.pages_succeeded += len(successful_results)
        self.stats.pages_failed += len(urls) - len(successful_results)
        
        batch_time = time.time() - batch_start_time
        batch_speed = len(urls) / batch_time if batch_time > 0 else 0
        
        logger.info(f"배치 처리 완료: {len(successful_results)}/{len(urls)} 성공, "
                   f"{batch_speed:.1f} 페이지/초")
        
        return successful_results

    async def _process_batch_results(self, batch_results: List[Dict]):
        """배치 결과 처리 및 새 링크 발견"""
        new_links_count = 0
        saved_count = 0
        
        for page_data in batch_results:
            if not page_data or not page_data.get('main_text'):
                continue
            
            url = page_data['url']
            content_text = page_data['main_text']
            
            # 콘텐츠 변경 확인
            if not self.processed_ledger.has_changed(url, content_text):
                self.stats.pages_skipped_unchanged += 1
                logger.debug(f"콘텐츠 변경 없음, 저장 건너뛰: {url}")
                continue
            
            # 데이터 저장
            self._save_crawled_data(page_data)
            self.processed_ledger.add_processed_item(url, content_text)
            saved_count += 1
            
            # 새 링크 발견 및 큐 추가
            links = page_data.get('links', [])
            self.stats.total_links_found += len(links)
            
            for link_url, link_text in links:
                if self._should_add_to_queue(link_url):
                    self.pending_urls.append(link_url)
                    self.visited_urls.add(link_url)
                    new_links_count += 1
        
        logger.info(f"배치 결과 처리: {saved_count}개 저장, {new_links_count}개 새 링크 발견")
        self.stats.pages_discovered += new_links_count

    def _should_add_to_queue(self, url: str) -> bool:
        """URL을 큐에 추가할지 판단"""
        if url in self.visited_urls or url in self.failed_urls:
            return False
            
        if not is_valid_url(url, self.base_netloc):
            return False
            
        # 큐 크기 제한 (메모리 보호)
        if len(self.pending_urls) > 10000:  # 최대 10,000개 URL까지 큐에 보관
            return False
            
        return True

    def _save_crawled_data(self, page_data: dict):
        """크롤링 데이터 저장 (고성능 버전)"""
        timestamp = int(time.time() * 1000)
        file_id = f"{timestamp}_{self.stats.pages_succeeded}.json"
        output_path = self.output_dir / file_id
        
        data_to_save = {
            "source_info": self.config,
            "crawled_content": {
                "url": page_data['url'],
                "title": page_data['title'],
                "extracted_text": page_data['main_text']
            },
            "metadata": {
                "crawl_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "processing_order": self.stats.pages_succeeded,
                "batch_processed": True
            }
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"파일 저장 실패 {output_path}: {e}")

    def _log_progress(self):
        """진행 상황 로깅"""
        if self.stats.pages_processed % 100 == 0:  # 100개마다 로깅
            max_pages = self.config.get("max_pages_to_crawl", 2000)
            progress_pct = (self.stats.pages_processed / max_pages) * 100
            
            logger.info(f"[{self.site_identifier}] 진행률: {progress_pct:.1f}% "
                       f"({self.stats.pages_processed}/{max_pages})")
            logger.info(f"성공률: {self.stats.success_rate():.1f}%, "
                       f"큐 크기: {len(self.pending_urls)}, "
                       f"평균 속도: {self.stats.avg_speed:.1f} 페이지/초")

    def _log_final_statistics(self):
        """최종 통계 로깅"""
        stats_dict = self.stats.to_dict()
        
        logger.info(f"[{self.site_identifier}] 최종 크롤링 통계:")
        logger.info(f"  총 처리 시간: {self.stats.processing_time:.2f}초")
        logger.info(f"  처리된 페이지: {self.stats.pages_processed}개")
        logger.info(f"  성공한 페이지: {self.stats.pages_succeeded}개")
        logger.info(f"  실패한 페이지: {self.stats.pages_failed}개")
        logger.info(f"  건너뛴 페이지: {self.stats.pages_skipped_unchanged + self.stats.pages_skipped_by_kb + self.stats.pages_skipped_problematic}개")
        logger.info(f"  발견된 링크: {self.stats.total_links_found}개")
        logger.info(f"  평균 처리 속도: {self.stats.avg_speed:.2f} 페이지/초")
        logger.info(f"  성공률: {self.stats.success_rate():.1f}%")
        
        # 성능 통계를 JSON 파일로 저장
        stats_file = self.output_dir / "crawling_stats.json"
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats_dict, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"통계 파일 저장 실패: {e}")

# ==========================================
# 기존 FastCrawlerAgent 호환 래퍼
# ==========================================

class SuperFastCrawlerAgent:
    """
    기존 FastCrawlerAgent와 완전 호환되는 고성능 래퍼
    기존 코드 수정 없이 즉시 성능 향상 적용 가능
    """
    
    def __init__(self, config: Dict):
        # 고성능 에이전트로 내부 구현
        self.hp_agent = HighPerformanceCrawlerAgent(config)
        
        # 기존 인터페이스 호환을 위한 속성들
        self.config = config
        self.site_identifier = config["site_identifier"]
        self.base_url = config["base_url"]
        
    async def run(self):
        """기존 run() 메서드와 동일한 인터페이스"""
        return await self.hp_agent.run()
    
    def log_performance(self):
        """기존 log_performance() 메서드 호환"""
        self.hp_agent._log_final_statistics()

# ==========================================
# 메인 실행 스크립트 업데이트
# ==========================================

async def run_high_performance_crawlers():
    """
    고성능 크롤러 실행 스크립트
    기존 run_crawlers.py를 대체하는 고성능 버전
    """
    import sys
    sys.path.append('.')
    
    from src.config import load_configs_from_prompt_xlsx
    
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - [HP-CRAWLER] %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Excel 파일에서 설정 로드
    configs = load_configs_from_prompt_xlsx()
    if not configs:
        logger.error("처리할 사이트 설정이 없습니다.")
        return

    logger.info(f"🚀 고성능 크롤러 시작: {len(configs)}개 사이트 대상")
    logger.info("📊 예상 처리 능력: 2000+ 페이지/사이트, 5-15 페이지/초")
    
    total_start_time = time.time()
    
    # 사이트별 순차 처리 (메모리 효율성을 위해)
    # 필요시 병렬 처리로 변경 가능
    for i, config in enumerate(configs, 1):
        site_start_time = time.time()
        logger.info(f"[{i}/{len(configs)}] {config['site_name']} 처리 시작...")
        
        agent = HighPerformanceCrawlerAgent(config)
        try:
            await agent.run()
        except Exception as e:
            logger.error(f"사이트 {config['site_name']} 처리 실패: {e}", exc_info=True)
        
        site_time = time.time() - site_start_time
        logger.info(f"[{i}/{len(configs)}] {config['site_name']} 완료 ({site_time:.1f}초)")
    
    total_time = time.time() - total_start_time
    logger.info(f"🎉 전체 크롤링 완료! 총 소요 시간: {total_time/60:.1f}분")

# ==========================================
# 성능 테스트 및 벤치마크
# ==========================================

async def benchmark_performance():
    """성능 벤치마크 테스트"""
    logger.info("🧪 성능 벤치마크 시작...")
    
    # 테스트 설정
    test_config = {
        "site_identifier": "performance_test",
        "site_name": "성능 테스트 사이트",
        "base_url": "https://example.com",
        "instruction_prompt": "성능 테스트용 크롤링",
        "max_pages_to_crawl": 500,  # 테스트용 500페이지
        "crawl_delay": 0.1
    }
    
    # 기존 버전과 고성능 버전 비교
    logger.info("1️⃣ 고성능 버전 테스트...")
    hp_start = time.time()
    
    hp_agent = HighPerformanceCrawlerAgent(test_config)
    await hp_agent.run()
    
    hp_time = time.time() - hp_start
    hp_stats = hp_agent.stats
    
    logger.info(f"고성능 버전 결과:")
    logger.info(f"  처리 시간: {hp_time:.2f}초")
    logger.info(f"  처리 속도: {hp_stats.avg_speed:.2f} 페이지/초")
    logger.info(f"  성공률: {hp_stats.success_rate():.1f}%")
    
    return {
        "hp_time": hp_time,
        "hp_speed": hp_stats.avg_speed,
        "hp_success_rate": hp_stats.success_rate()
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "benchmark":
        # 성능 벤치마크 실행
        asyncio.run(benchmark_performance())
    else:
        # 일반 크롤링 실행
        asyncio.run(run_high_performance_crawlers())

import asyncio
import json
import logging
from pathlib import Path
import time
import aiofiles
import re

from src.llm.llm_client import LlmClient
from src.packet.data_packet import create_data_packet
from src.feedback.knowledge_base import KnowledgeBase
from src.feedback.processed_ledger import ProcessedLedger
from config.settings import config

logger = logging.getLogger(__name__)

class LlmProcessingWorker:
    """
    [v2.0] '3단계 검증' (품질 검사 -> 관련성 검사 -> 심층 분석) 로직을 적용하여
    데이터 처리의 정확성과 효율성을 극대화한 최종 워커.
    """
    def __init__(self, site_identifier: str):
        self.site_identifier = site_identifier
        self.relevance_threshold = config.relevance_threshold
        self.input_dir = Path("crawled_data") / self.site_identifier
        self.processed_dir = self.input_dir / "processed"
        self.rejected_dir = self.input_dir / "rejected"
        self.output_dir = Path("output_packets") / self.site_identifier
        for d in [self.input_dir, self.processed_dir, self.rejected_dir, self.output_dir]:
            d.mkdir(parents=True, exist_ok=True)
        self.llm_client = LlmClient()
        self.knowledge_base = KnowledgeBase(site_identifier=self.site_identifier)
        self.processed_ledger = ProcessedLedger(site_identifier=self.site_identifier)
        self.stats = {"processed": 0, "accepted": 0, "rejected": 0, "parsing_failures": 0, "quality_rejected": 0, "gatekeeper_rejected": 0}
        logger.info(f"[{self.site_identifier}] LlmProcessingWorker 초기화 완료.")

    def _is_low_quality_text(self, text: str) -> bool:
        """ [신규] LLM 호출 전, 텍스트가 목록형 데이터처럼 보이는지 프로그래밍 방식으로 검사합니다. """
        lines = text.split('\n')
        if len(lines) < 5: return False # 너무 짧은 텍스트는 판단 보류

        short_line_count = 0
        date_pattern = r'\d{4}-\d{2}-\d{2}' # YYYY-MM-DD 형식의 날짜 패턴

        for line in lines:
            if len(line.strip()) < 50: # 50자 미만의 짧은 줄
                short_line_count += 1
            # 날짜 패턴이 포함된 줄도 목록의 특징으로 간주
            if re.search(date_pattern, line):
                short_line_count += 0.5 # 가중치 부여

        # 전체 줄의 70% 이상이 짧은 줄이거나 날짜를 포함하면 저품질(목록)로 판단
        if (short_line_count / len(lines)) > 0.7:
            return True

        return False

    async def run(self):
        logger.info(f"[{self.site_identifier}] LLM 워커가 실시간 감시를 시작합니다.")
        try:
            while True:
                processed_in_cycle = await self._scan_and_process_once()
                if processed_in_cycle == 0: await asyncio.sleep(15)
                else: await asyncio.sleep(2)
        except asyncio.CancelledError:
             logger.info(f"[{self.site_identifier}] 워커가 종료됩니다.")
        finally:
            logger.info(f"[{self.site_identifier}] 최종 통계: {json.dumps(self.stats, indent=2, ensure_ascii=False)}")

    async def _scan_and_process_once(self) -> int:
        files = [f for f in self.input_dir.iterdir() if f.is_file() and f.suffix == '.json']
        if not files: return 0
        logger.info(f"[{self.site_identifier}] {len(files)}개의 새 파일을 처리합니다.")
        tasks = [self._process_file(f) for f in files]
        await asyncio.gather(*tasks)
        return len(files)

    async def _process_file(self, file_path: Path):
        """ [수정됨] 3단계 검증 로직을 사용하여 파일을 처리합니다. """
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.loads(await f.read())
            url = raw_data['crawled_content']['url']
            text = raw_data['crawled_content']['extracted_text']
            prompt = raw_data['source_info']['instruction_prompt']

            # --- 검증 0단계: 파싱 실패 여부 판단 ---
            if "--- 첨부 파일 처리 실패:" in text:
                self.knowledge_base.update_failure(url)
                self.stats["parsing_failures"] += 1
                await self._reject_and_archive(file_path, reason="첨부 파일 파싱 실패")
                return

            # --- [신규] 검증 1단계: 프로그래밍 방식 품질 검사 ---
            if self._is_low_quality_text(text):
                logger.warning(f"📉 품질 검사: 목록형 데이터로 추정되어 폐기 - {url}")
                self.knowledge_base.update_score(url, 0.0) # 저품질이므로 0점 학습
                self.stats["quality_rejected"] += 1
                await self._reject_and_archive(file_path, "프로그램에 의해 저품질(목록형)으로 분류됨")
                return

            # --- 검증 2단계: LLM 게이트키퍼를 통한 빠른 관련성 검사 ---
            if not await self.llm_client.is_content_relevant(text, prompt):
                logger.info(f"🚫 LLM 게이트키퍼: 관련 없는 콘텐츠로 판단하여 폐기 - {url}")
                self.knowledge_base.update_score(url, 0.0)
                self.stats["gatekeeper_rejected"] += 1
                await self._reject_and_archive(file_path, "LLM에 의해 관련성 없음으로 분류됨")
                return

            # --- 검증 3단계: 관련성 있는 콘텐츠에 대해서만 심층 분석 수행 ---
            logger.info(f"✅ LLM 게이트키퍼 통과: 심층 분석 시작 - {url}")
            llm_result = await self.llm_client.evaluate_and_enhance_content(text, prompt)
            score = llm_result.get('relevance_score', 0.0)
            self.knowledge_base.update_score(url, score)

            if score >= self.relevance_threshold:
                await self._accept_and_package(raw_data, llm_result, file_path)
            else:
                await self._reject_and_archive(file_path, f"낮은 관련성 점수: {score:.2f}")

        except Exception as e:
            logger.error(f"파일 처리 실패: {file_path}. 원인: {e}", exc_info=True)
            if 'url' in locals(): self.knowledge_base.update_failure(url)
            await self._reject_and_archive(file_path, f"처리 중 오류 발생: {e}")

    async def _accept_and_package(self, raw_data: dict, llm_result: dict, original_path: Path):
        final_packet = create_data_packet(
            agent_id="llm-worker-01", config=raw_data['source_info'], page_data=raw_data['crawled_content'],
            extracted_text=raw_data['crawled_content']['extracted_text'],
            relevance_score=llm_result['relevance_score'], enhanced_data=llm_result
        )
        packet_filename = f"{int(time.time() * 1000)}_{original_path.stem}.json"
        output_filepath = self.output_dir / packet_filename
        try:
            async with aiofiles.open(output_filepath, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(final_packet, indent=2, ensure_ascii=False))
            logger.info(f"✅ 패킷 저장 완료 (점수: {llm_result['relevance_score']:.2f}): {output_filepath.name}")
        except Exception as e:
            logger.error(f"패킷 저장 실패: {e}")

        self.processed_ledger.add_processed_item(raw_data['crawled_content']['url'], raw_data['crawled_content']['extracted_text'])
        self.stats["processed"] += 1
        self.stats["accepted"] += 1
        await self._move_file(original_path, self.processed_dir)

    async def _reject_and_archive(self, file_path: Path, reason: str):
        logger.warning(f"콘텐츠 폐기: {file_path.name}. 원인: {reason}")
        self.stats["processed"] += 1
        self.stats["rejected"] += 1
        await self._move_file(file_path, self.rejected_dir)

    async def _move_file(self, src: Path, dest_dir: Path):
        try:
            src.rename(dest_dir / src.name)
        except Exception as e:
            logger.error(f"파일 이동 실패: {src} -> {dest_dir / src.name}, 원인: {e}")


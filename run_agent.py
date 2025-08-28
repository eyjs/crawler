# run_agent.py (Output 및 Log 폴더 구조가 개선된 최종 버전)

import asyncio
import pandas as pd
from loguru import logger
import sys
from datetime import datetime
from urllib.parse import urlparse
import json
import os
from dataclasses import asdict

# 프로젝트 루트 경로 추가
sys.path.append('.')

from src.agent.autonomous_agent import AutonomousAgent

def find_and_validate_input_file():
    input_dir = 'input'; EXPECTED_COLUMNS_COUNT = 3
    if not os.path.exists(input_dir):
        logger.error("❌ 'input' 폴더를 찾을 수 없습니다."); return None
    xlsx_files = [f for f in os.listdir(input_dir) if f.endswith('.xlsx')]
    if not xlsx_files:
        logger.error("❌ 'input' 폴더에 .xlsx 파일이 없습니다."); return None
    file_path = os.path.join(input_dir, xlsx_files[0])
    logger.info(f"🔍 입력 파일 발견: '{file_path}'")
    try:
        df = pd.read_excel(file_path, header=None)
        if len(df.columns) < EXPECTED_COLUMNS_COUNT:
            logger.error(f"❌ 입력 파일 양식 오류: 최소 {EXPECTED_COLUMNS_COUNT}개의 컬럼이 필요합니다."); return None
        df_required = df.iloc[1:, :EXPECTED_COLUMNS_COUNT]
        df_required.columns = ['기관/단체/회사', '주요 내용', '웹사이트 주소']
        df_validated = df_required.dropna()
        if df_validated.empty:
            logger.error("❌ 처리할 유효한 데이터가 없습니다."); return None
        logger.success("✅ 입력 파일 양식이 올바릅니다 (컬럼 순서 기준).")
        return file_path, df_validated
    except Exception as e:
        logger.error(f"❌ 입력 파일('{file_path}')을 읽는 중 오류가 발생했습니다: {e}"); return None


def save_results_to_file(domain: str, packets: list):
    """
    크롤링 결과를 'output/년-월-일/사이트명/' 폴더에 개별 JSON 파일로 저장합니다.
    """
    if not packets:
        logger.warning(f"[{domain}] 저장할 데이터 패킷이 없습니다.")
        return

    date_str = datetime.now().strftime("%Y-%m-%d")
    site_output_dir = os.path.join("output", date_str, domain)
    os.makedirs(site_output_dir, exist_ok=True)

    saved_count = 0
    for packet in packets:
        file_path = os.path.join(site_output_dir, f"{packet.packet_id}.json")
        packet_as_dict = asdict(packet)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(packet_as_dict, f, ensure_ascii=False, indent=2)
            saved_count += 1
        except Exception as e:
            logger.error(f"💾 개별 패킷 파일 저장 실패: {file_path} | 오류: {e}")

    logger.success(f"💾 최종 결과 저장 완료: {site_output_dir} ({saved_count}/{len(packets)}개 패킷)")


async def main():
    """자율 에이전트 실행 메인 함수"""

    logger.remove()
    logger.add(sys.stderr, level="INFO")

    validation_result = find_and_validate_input_file()
    if not validation_result:
        return

    config_file_path, config_df = validation_result
    targets = config_df.to_dict('records')
    logger.info(f"✅ 입력 파일('{config_file_path}') 로드 완료. {len(targets)}개의 사이트를 크롤링합니다.")

    for target in targets:
        site_name = target['기관/단체/회사']
        site_url = target['웹사이트 주소']
        prompt = target['주요 내용']

        if not str(site_url).startswith('http'):
            site_url = 'https://' + str(site_url)

        domain = urlparse(site_url).netloc

        # --- 로그 폴더 구조가 변경되었습니다 ---
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_dir = os.path.join("logs", date_str)
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, f"{domain}.log")
        # ------------------------------------

        log_sink_id = logger.add(log_file_path, level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}", encoding='utf-8', enqueue=True)

        logger.info(f"▶️  '{prompt}' 목표로 크롤링 시작: {site_url}")
        logger.info(f"📜 로그 파일 생성: {log_file_path}")

        agent = AutonomousAgent(start_url=site_url, instruction_prompt=prompt, site_name=site_name)
        crawled_packets = await agent.run()

        save_results_to_file(domain, crawled_packets)

        logger.remove(log_sink_id)

        logger.info("-" * 50)
        await asyncio.sleep(5)

    logger.info("🎉 모든 작업이 완료되었습니다.")


if __name__ == "__main__":
    asyncio.run(main())
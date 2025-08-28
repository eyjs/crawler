# run_agent.py (수정된 최종 버전)

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
    """
    'input' 폴더에서 .xlsx 파일을 찾아 컬럼 순서(인덱스) 기준으로 유효성을 검증합니다.
    """
    input_dir = 'input'

    # 이제 컬럼 이름 대신 순서(인덱스)가 중요합니다.
    # 0: 기관/단체/회사 (메타데이터)
    # 1: 웹사이트 주소 (URL)
    # 2: 주요 내용 (프롬프트 지침)
    EXPECTED_COLUMNS_COUNT = 3

    if not os.path.exists(input_dir):
        logger.error(f"❌ 'input' 폴더를 찾을 수 없습니다. 프로젝트 루트에 생성해주세요.")
        return None

    xlsx_files = [f for f in os.listdir(input_dir) if f.endswith('.xlsx')]

    if not xlsx_files:
        logger.error(f"❌ 'input' 폴더에 크롤링 대상을 정의한 .xlsx 파일이 없습니다.")
        return None

    file_path = os.path.join(input_dir, xlsx_files[0])
    logger.info(f"🔍 입력 파일 발견: '{file_path}'")

    try:
        df = pd.read_excel(file_path, header=None) # 헤더가 없다고 가정하고 첫 줄부터 읽음

        if len(df.columns) < EXPECTED_COLUMNS_COUNT:
            logger.error(f"❌ 입력 파일 양식 오류: 최소 {EXPECTED_COLUMNS_COUNT}개의 컬럼이 필요합니다.")
            logger.error(f"💡 엑셀 파일에 [기관/단체/회사], [웹사이트 주소], [주요 내용] 순서로 데이터가 있는지 확인하세요.")
            return None

        # 첫 3개 컬럼만 인덱스로 선택
        df_required = df.iloc[:, :EXPECTED_COLUMNS_COUNT]

        # 내부적으로 사용할 표준 컬럼명 지정
        df_required.columns = ['기관/단체/회사', '웹사이트 주소', '주요 내용']

        # 필수 컬럼에 빈 값이 있는 행 제거
        df_validated = df_required.dropna()

        if len(df_validated) < len(df_required):
            logger.warning(f"⚠️ 입력 파일의 일부 행에 빈 값이 있어 제외되었습니다 ({len(df_required) - len(df_validated)}개 행).")

        logger.success("✅ 입력 파일 양식이 올바릅니다 (컬럼 순서 기준).")
        return file_path, df_validated

    except Exception as e:
        logger.error(f"❌ 입력 파일('{file_path}')을 읽는 중 오류가 발생했습니다: {e}")
        return None


def save_results_to_file(domain: str, packets: list):
    """크롤링 결과를 사이트별 JSON 파일로 저장합니다."""
    if not packets:
        logger.warning(f"[{domain}] 저장할 데이터 패킷이 없습니다. 파일이 생성되지 않습니다.")
        return

    output_dir = "crawled_results"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(output_dir, f"{domain}_{timestamp}.json")

    packets_as_dicts = [asdict(packet) for packet in packets]

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(packets_as_dicts, f, ensure_ascii=False, indent=2)
        logger.success(f"💾 최종 결과 저장 완료: {file_path} ({len(packets)}개 패킷)")
    except Exception as e:
        logger.error(f"💾 파일 저장 실패: {file_path} | 오류: {e}")


async def main():
    """자율 에이전트 실행 메인 함수"""

    logger.remove()
    logger.add(sys.stderr, level="INFO")

    # 1. 입력 파일 찾기 및 유효성 검증
    validation_result = find_and_validate_input_file()
    if not validation_result:
        return

    config_file_path, config_df = validation_result
    targets = config_df.to_dict('records')
    logger.info(f"✅ 입력 파일('{config_file_path}') 로드 완료. {len(targets)}개의 사이트를 크롤링합니다.")

    # 2. 각 사이트에 대해 에이전트 실행
    for target in targets:
        # 이제 인덱스로 데이터를 가져왔으므로, 키는 우리가 지정한 표준 이름을 사용
        site_name = target['기관/단체/회사']
        site_url = target['웹사이트 주소']
        prompt = target['주요 내용']

        if not str(site_url).startswith('http'):
            site_url = 'https://' + str(site_url)

        domain = urlparse(site_url).netloc
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = f"logs/{domain}_{timestamp}.log"

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
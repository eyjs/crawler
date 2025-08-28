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

def save_results_to_file(domain: str, packets: list):
    """크롤링 결과를 사이트별 JSON 파일로 저장합니다."""
    if not packets:
        logger.warning(f"[{domain}] 저장할 데이터 패킷이 없습니다. 파일이 생성되지 않습니다.")
        return

    output_dir = "crawled_results"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(output_dir, f"{domain}_{timestamp}.json")

    # dataclass 객체 리스트를 JSON 직렬화 가능한 dict 리스트로 변환
    packets_as_dicts = [asdict(packet) for packet in packets]

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(packets_as_dicts, f, ensure_ascii=False, indent=2)
        logger.success(f"💾 최종 결과 저장 완료: {file_path} ({len(packets)}개 패킷)")
    except Exception as e:
        logger.error(f"💾 파일 저장 실패: {file_path} | 오류: {e}")


async def main():
    """자율 에이전트 실행 메인 함수"""

    # 기본 터미널 로거 설정
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    # 1. 설정 파일 로드
    try:
        config_file_name = "금융_재테크_은퇴설계_웹사이트_통합_크롤링앤스크래핑2025.-8.-27.xlsx"
        config_df = pd.read_excel(config_file_name)
        # 엑셀 파일에서 '기관/단체/회사' 컬럼도 함께 읽어옵니다.
        targets = config_df[['기관/단체/회사', '웹사이트 주소', '주요 내용']].dropna().to_dict('records')
        logger.info(f"✅ 엑셀 설정 파일('{config_file_name}') 로드 완료. {len(targets)}개의 사이트를 크롤링합니다.")
    except Exception as e:
        logger.error(f"❌ 설정 파일 로드 실패: {e}")
        return

    # 2. 각 사이트에 대해 에이전트 실행
    for target in targets:
        site_name = target['기관/단체/회사']
        site_url = target['웹사이트 주소']
        prompt = target['주요 내용']

        if not site_url.startswith('http'):
            site_url = 'https://' + site_url

        domain = urlparse(site_url).netloc
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = f"logs/{domain}_{timestamp}.log"

        log_sink_id = logger.add(log_file_path, level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}", encoding='utf-8', enqueue=True)

        logger.info(f"▶️  '{prompt}' 목표로 크롤링 시작: {site_url}")
        logger.info(f"📜 로그 파일 생성: {log_file_path}")

        # 에이전트 초기화 시 site_name을 전달합니다.
        agent = AutonomousAgent(start_url=site_url, instruction_prompt=prompt, site_name=site_name)
        crawled_packets = await agent.run()

        # --- 크롤링 결과 파일 저장 ---
        save_results_to_file(domain, crawled_packets)
        # ---------------------------

        logger.remove(log_sink_id)

        logger.info("-" * 50)
        await asyncio.sleep(5)

    logger.info("🎉 모든 작업이 완료되었습니다.")

if __name__ == "__main__":
    asyncio.run(main())
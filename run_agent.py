# run_agent.py

import asyncio
import pandas as pd
from loguru import logger
import sys

# 프로젝트 루트 경로 추가 (터미널에서 바로 실행 가능하도록)
sys.path.append('.')

from src.agent.autonomous_agent import AutonomousAgent

async def main():
    """자율 에이전트 실행 메인 함수"""

    # 1. 설정 파일 로드
    try:
        # 사용자가 업로드한 CSV 파일명을 사용합니다.
        config_df = pd.read_csv("금융_재테크_은퇴설계_웹사이트_통합_크롤링앤스크래핑2025.-8.-27.xlsx - Sheet1.csv")
        # 컬럼명이 파일과 일치하는지 확인 (웹사이트 주소, 주요 내용)
        targets = config_df[['웹사이트 주소', '주요 내용']].dropna().to_dict('records')
        logger.info(f"✅ 설정 파일 로드 완료. {len(targets)}개의 사이트를 크롤링합니다.")
    except FileNotFoundError:
        logger.error("❌ 설정 파일('금융_재테크_은퇴설계_웹사이트_통합_크롤링앤스크래핑2025.-8.-27.xlsx - Sheet1.csv')을 찾을 수 없습니다.")
        return
    except Exception as e:
        logger.error(f"❌ 설정 파일 로드 실패: {e}")
        return

    # 2. 각 사이트에 대해 에이전트 실행
    for target in targets:
        site_url = target['웹사이트 주소']
        prompt = target['주요 내용']

        if not site_url.startswith('http'):
            site_url = 'https://' + site_url

        logger.info(f"▶️  '{prompt}' 목표로 크롤링 시작: {site_url}")

        agent = AutonomousAgent(start_url=site_url, instruction_prompt=prompt)
        await agent.run()

        logger.info("-" * 50)
        # 다음 사이트 크롤링 전 잠시 대기
        await asyncio.sleep(5)

    logger.info("🎉 모든 작업이 완료되었습니다.")

if __name__ == "__main__":
    # 로그 레벨 설정 (DEBUG로 하면 링크 평가 점수를 모두 볼 수 있습니다)
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    asyncio.run(main())
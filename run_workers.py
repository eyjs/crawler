# run_workers.py

import asyncio
import logging
import argparse
from pathlib import Path
from src.agent.llm_processing_worker import LlmProcessingWorker

async def main():
    """
    지정된 사이트(들)에 대한 LLM 워커를 실행하는 메인 함수.
    워커는 중지하기 전까지 계속 실행됩니다.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [WORKER] %(message)s')
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="LLM Processing Worker 실행 스크립트")
    parser.add_argument(
        "site_identifiers",
        nargs='*', # 여러 사이트 ID를 받을 수 있도록 설정
        help="처리할 사이트의 식별자 (e.g., miraeasset_retirement kyobo_life). 비워두면 crawled_data 폴더의 모든 사이트를 대상으로 함."
    )
    args = parser.parse_args()

    site_ids_to_process = args.site_identifiers
    # 만약 특정 사이트 ID가 주어지지 않았다면, crawled_data 폴더에 있는 모든 디렉토리를 대상으로 함
    if not site_ids_to_process:
        crawled_data_dir = Path("crawled_data")
        if crawled_data_dir.exists():
            site_ids_to_process = [d.name for d in crawled_data_dir.iterdir() if d.is_dir()]

    if not site_ids_to_process:
        logger.warning("처리할 사이트가 없습니다. crawled_data 폴더에 데이터가 있는지 확인하세요.")
        return

    logger.info(f"다음 사이트들에 대한 LLM 워커를 시작합니다: {', '.join(site_ids_to_process)}")

    # 각 사이트에 대한 워커를 생성하여 동시에 실행
    tasks = [LlmProcessingWorker(site_id).run() for site_id in site_ids_to_process]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nLLM 워커가 중지되었습니다.")
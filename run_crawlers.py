# run_crawlers.py

import asyncio
import logging
from src.agent.fast_crawler_agent import FastCrawlerAgent
from src.config import load_configs_from_prompt_xlsx

async def main():
    """
    설정된 모든 사이트에 대한 크롤러를 동시에 실행하는 메인 함수.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [CRAWLER] %(message)s')
    logger = logging.getLogger(__name__)

    # 1. Excel 파일에서 설정 로드
    configs = load_configs_from_prompt_xlsx()
    if not configs:
        logger.error("처리할 사이트 설정이 없습니다. 크롤러를 종료합니다.")
        return

    logger.info(f"{len(configs)}개 사이트에 대한 병렬 크롤링을 시작합니다.")

    # 2. 모든 사이트에 대한 크롤러 태스크를 생성하여 동시에 실행
    tasks = [FastCrawlerAgent(config).run() for config in configs]
    await asyncio.gather(*tasks)

    logger.info("모든 크롤링 작업이 완료되었습니다.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n크롤러가 중지되었습니다.")
# run_agent.py (로그 경로 오류를 수정한 최종 버전)

import asyncio
import pandas as pd
from loguru import logger
import sys
from datetime import datetime
from urllib.parse import urlparse
import json
import os
from pathlib import Path # Added this line
from dataclasses import asdict

# Windows 콘솔 한글 출력 문제 해결
if os.name == 'nt':  # Windows
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 프로젝트 루트 경로 추가
sys.path.append('.')

from src.agent.autonomous_agent import AutonomousAgent
from src.utils.ollama_manager import OllamaManager, check_env_local

def setup_loggers(log_dir: str):
    """기본 로거(콘솔, 시스템 파일)를 설정합니다."""
    logger.remove()
    # 콘솔에는 INFO 레벨 이상의 로그만 출력
    logger.add(sys.stderr, level="INFO")

    # --- 이 부분이 수정되었습니다 ---
    # 이제 system.log도 날짜별 폴더 안에 생성됩니다.
    system_log_path = os.path.join(log_dir, "system.log")
    # -----------------------------

    logger.add(system_log_path, level="DEBUG", rotation="10 MB", retention=5,
               format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {process.id} | {name}:{function}:{line} - {message}",
               encoding='utf-8', enqueue=True)
    logger.info(f"기본 로거 설정 완료. 상세 로그는 '{system_log_path}'에 기록됩니다.")

def find_and_validate_input_file():
    input_dir = 'input'; EXPECTED_COLUMNS_COUNT = 3
    if not os.path.exists(input_dir):
        logger.error(f"❌ 'input' 폴더를 찾을 수 없습니다."); return None
    xlsx_files = [f for f in os.listdir(input_dir) if f.endswith('.xlsx')]
    if not xlsx_files:
        logger.error(f"❌ 'input' 폴더에 .xlsx 파일이 없습니다."); return None
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

def check_ollama_service():
    """로컬 LLM 모드 사용 시 Ollama 서비스를 확인하고 시작합니다."""
    if not check_env_local():
        return True  # 로컬 모드가 아니면 확인 불필요
    
    logger.info("🤖 로컬 LLM 모드 감지 - Ollama 서비스 확인 중...")
    
    ollama_manager = OllamaManager()
    
    # Ollama 설치 확인
    if not ollama_manager.check_ollama_installed():
        logger.error("❌ Ollama가 설치되어 있지 않습니다.")
        logger.info("💡 해결 방법:")
        logger.info("   1. setup.bat을 다시 실행하여 자동 설치")
        logger.info("   2. 또는 https://ollama.ai/download 에서 수동 설치")
        return False
    
    # Ollama 서비스 실행 확인 및 시작
    if not ollama_manager.check_ollama_running():
        logger.info("🚀 Ollama 서비스 시작 중...")
        if not ollama_manager.start_ollama_service():
            logger.error("❌ Ollama 서비스 시작에 실패했습니다.")
            logger.info("💡 수동으로 터미널에서 'ollama serve' 명령을 실행해보세요.")
            return False
    
    # 모델 확인
    if not ollama_manager.check_model_installed():
        logger.warning("⚠️ Llama3 모델이 설치되어 있지 않습니다.")
        logger.info("💡 모델을 설치하려면 터미널에서 'ollama pull llama3' 명령을 실행하세요.")
        return False
    
    logger.success("✅ Ollama/Llama3 환경 준비 완료!")
    return True

def save_results_to_file(domain: str, packets: list, date_str: str):
    if not packets:
        logger.warning(f"[{domain}] 저장할 데이터 패킷이 없습니다.")
        return
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
    logger.info("🚀 LLM Crawler Agent 시작")
    
    try:
        # 배포 환경 초기화 (배포 시에만)
        if getattr(sys, 'frozen', False):  # exe 환경
            from src.utils.deployment_utils import initialize_deployment_environment
            path_manager = initialize_deployment_environment()
        else:
            # 개발 환경에서는 기본 폴더 생성
            for directory in ['input', 'output', 'logs']:
                Path(directory).mkdir(exist_ok=True)
        
        # 날짜별 로그 디렉토리 설정
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_dir = os.path.join("logs", date_str)
        os.makedirs(log_dir, exist_ok=True)
        setup_loggers(log_dir)
    except Exception as e:
        logger.error(f"❌ 초기화 중 오류가 발생했습니다: {e}")
        input("Enter 키를 눌러 종료...")
        return
    
    # 로컬 LLM 서비스 확인 (필요한 경우)
    if not check_ollama_service():
        logger.error("❌ 로컬 LLM 환경 준비에 실패했습니다.")
        logger.info("💡 .env 파일에서 LLM_PROVIDER를 'gemini'로 변경하거나 Ollama를 설치해주세요.")
        input("Enter 키를 눌러 종료...")
        return

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

        # 사이트별 로그 파일 경로 설정
        log_file_path = os.path.join(log_dir, f"{domain}.log")

        log_sink_id = logger.add(log_file_path, level="INFO",
                                 format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
                                 encoding='utf-8', enqueue=True)

        logger.info(f"▶️ '{prompt}' 목표로 크롤링 시작: {site_url}")

        agent = AutonomousAgent(start_url=site_url, instruction_prompt=prompt, site_name=site_name)
        crawled_packets = await agent.run()

        save_results_to_file(domain, crawled_packets, date_str)

        logger.remove(log_sink_id)

        logger.info("-" * 50)
        await asyncio.sleep(5)

    logger.info("🎉 모든 작업이 완료되었습니다.")

def check_dependencies():
    """필수 의존성 확인"""
    missing_packages = []
    
    try:
        import pandas
    except ImportError:
        missing_packages.append("pandas")
    
    try:
        import openpyxl
    except ImportError:
        missing_packages.append("openpyxl")
    
    try:
        import aiohttp
    except ImportError:
        missing_packages.append("aiohttp")
    
    # 로컬 LLM 사용 시 ollama 패키지 확인
    if check_env_local():
        try:
            import ollama
        except ImportError:
            missing_packages.append("ollama")
    
    if missing_packages:
        logger.error(f"❌ 필수 패키지가 설치되어 있지 않습니다: {', '.join(missing_packages)}")
        logger.info(f"💡 설치 명령: pip install {' '.join(missing_packages)}")
        logger.info("💡 또는 setup.bat을 실행하여 환경을 재구성하세요.")
        return False
    
    return True

if __name__ == "__main__":
    # 의존성 확인
    if not check_dependencies():
        input("Enter 키를 눌러 종료...")
        sys.exit(1)
    
    # 메인 실행
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n프로그램이 중단되었습니다.")
    except Exception as e:
        logger.error(f"치명적 오류: {e}")
        input("Enter 키를 눌러 종료...")
        sys.exit(1)
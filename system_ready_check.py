#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SystemReadyCheck.py
LLM Crawler Agent 시스템 준비 상태 점검 도구
"""

import asyncio
import os
import sys
from loguru import logger
import requests
import pandas as pd



# 프로젝트 루트 경로 추가
sys.path.append('.')

class SystemHealthCheck:
    """
    크롤링 에이전트 시스템의 주요 구성 요소들의 상태를 점검합니다.
    """
    def __init__(self):
        self.results = {}
        logger.remove()
        logger.add(sys.stderr, level="INFO")

    def print_header(self):
        logger.info("=" * 50)
        logger.info("🚀 LLM Crawler Agent - 통합 시스템 점검 시작 🚀")
        logger.info("=" * 50)

    def print_footer(self):
        total_checks = len(self.results)
        passed_checks = sum(1 for status, msg in self.results.values() if status)

        logger.info("-" * 50)
        if passed_checks == total_checks:
            logger.success(f"✅ 모든 점검 통과 ({passed_checks}/{total_checks}) - 시스템이 정상 작동할 준비가 되었습니다.")
        else:
            logger.warning(f"⚠️ 일부 점검 실패 ({passed_checks}/{total_checks}) - 아래 실패 항목을 확인하세요.")
        logger.info("=" * 50)

    def record_result(self, check_name: str, status: bool, message: str):
        self.results[check_name] = (status, message)
        log_func = logger.success if status else logger.error
        log_func(f"[{'PASS' if status else 'FAIL'}] {check_name}: {message}")

    async def run_all_checks(self):
        self.print_header()

        if not self.check_config_file_exists():
            self.print_footer(); sys.exit(1)

        self.check_config_loading()
        self.check_directories()

        # --- 입력 파일 검증 기능 추가 ---
        self.check_input_file()
        # -----------------------------

        self.check_web_connection()
        await self.check_llm_connection()

        self.print_footer()

        all_passed = all(status for status, msg in self.results.values())
        sys.exit(0 if all_passed else 1)

    def check_config_file_exists(self) -> bool:
        config_path = os.path.join('config', 'settings.py')
        if os.path.exists(config_path):
            self.record_result("설정 파일 존재", True, f"'{config_path}' 파일이 존재합니다.")
            return True
        else:
            self.record_result("설정 파일 존재", False, f"필수 설정 파일인 '{config_path}'를 찾을 수 없습니다.")
            return False

    def check_config_loading(self):
        try:
            from config.settings import config
            self.record_result("설정 파일 로드", True, "'.env' 및 'settings.py'가 성공적으로 로드되었습니다.")
        except Exception as e:
            self.record_result("설정 파일 로드", False, f"설정 파일 로드 중 오류 발생: {e}")

    def check_directories(self):
        try:
            os.makedirs("output", exist_ok=True)
            self.record_result("필수 디렉토리", True, "'logs', 'output', 'input' 폴더를 사용 가능합니다.")
        except OSError as e:
            self.record_result("필수 디렉토리", False, f"디렉토리 생성 권한 오류: {e}")

    def check_input_file(self):
        """'input' 폴더에 유효한 .xlsx 파일이 있는지 점검합니다."""
        input_dir = 'input'

        xlsx_files = [f for f in os.listdir(input_dir) if f.endswith('.xlsx')]
        if not xlsx_files:
            self.record_result("입력 파일 존재", False, f"'input' 폴더에 .xlsx 파일이 없습니다. 크롤링 대상을 추가하세요.")
            return

        file_path = os.path.join(input_dir, xlsx_files[0])
        try:
            df = pd.read_excel(file_path, header=None)
            if len(df.columns) < 3:
                self.record_result("입력 파일 양식", False, f"'{xlsx_files[0]}' 파일에 최소 3개의 컬럼이 필요합니다.")
            else:
                self.record_result("입력 파일 양식", True, f"'{xlsx_files[0]}' 파일이 유효한 양식(최소 3개 컬럼)을 가집니다.")
        except Exception:
            self.record_result("입력 파일 양식", False, f"'{xlsx_files[0]}' 파일을 읽을 수 없습니다. 파일이 손상되었을 수 있습니다.")

    def check_web_connection(self):
        try:
            response = requests.get("https://example.com", timeout=10)
            if response.status_code == 200:
                self.record_result("기본 웹 연결", True, "'example.com'에 성공적으로 연결했습니다.")
            else:
                self.record_result("기본 웹 연결", False, f"HTTP 상태 코드가 {response.status_code} 입니다.")
        except requests.RequestException:
            self.record_result("기본 웹 연결", False, "외부 인터넷 연결에 실패했습니다.")

    async def check_llm_connection(self):
        # Dynamically import dependencies only when needed for the check
        try:
            from config.settings import config
            import ollama
            import google.generativeai as genai
        except ImportError as e:
            self.record_result("LLM 라이브러리", False, f"필수 LLM 라이브러리 로드 실패: {e}")
            return

        provider = config.llm_provider.lower()
        check_name = f"LLM 연결 ({provider.upper()})"

        if provider == "local":
            try:
                await ollama.AsyncClient().list()
                self.record_result(check_name, True, f"Ollama 서버에 성공적으로 연결했습니다 (모델: {config.local_llm_model}).")
            except Exception:
                self.record_result(check_name, False, "Ollama 서버에 연결할 수 없습니다. Ollama가 실행 중인지 확인하세요.")

        elif provider == "gemini":
            if not config.gemini_api_key or "여기에" in config.gemini_api_key:
                self.record_result(check_name, False, "GEMINI_API_KEY가 .env 파일에 설정되지 않았습니다.")
                return
            try:
                genai.configure(api_key=config.gemini_api_key)
                genai.list_models()
                self.record_result(check_name, True, "Gemini API 키가 유효하며, 서버에 연결되었습니다.")
            except Exception:
                self.record_result(check_name, False, f"Gemini API 연결에 실패했습니다. API 키가 올바른지 확인하세요.")


if __name__ == "__main__":
    health_checker = SystemHealthCheck()
    asyncio.run(health_checker.run_all_checks())
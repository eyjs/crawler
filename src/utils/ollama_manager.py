#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama/Llama3 설치 및 관리 유틸리티
로컬 LLM 환경 자동 구성
"""

import os
import sys
import platform
import subprocess
import requests
import time
from pathlib import Path
from loguru import logger
import json



class OllamaManager:
    """Ollama/Llama3 설치 및 관리 클래스"""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.ollama_base_url = "http://localhost:11434"
        self.model_name = "llama3"
        
    def check_ollama_installed(self):
        """Ollama가 설치되어 있는지 확인"""
        try:
            result = subprocess.run(['ollama', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"✅ Ollama 설치 확인: {version}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            pass
        
        logger.warning("⚠️ Ollama가 설치되어 있지 않습니다")
        return False
    
    def install_ollama(self):
        """플랫폼별 Ollama 설치"""
        logger.info(f"📦 {self.platform} 환경에 Ollama 설치 시작...")
        
        try:
            if self.platform == 'windows':
                return self._install_ollama_windows()
            elif self.platform == 'darwin':  # macOS
                return self._install_ollama_macos()
            elif self.platform == 'linux':
                return self._install_ollama_linux()
            else:
                logger.error(f"❌ 지원하지 않는 플랫폼: {self.platform}")
                return False
        except Exception as e:
            logger.error(f"❌ Ollama 설치 실패: {e}")
            return False
    
    def _install_ollama_windows(self):
        """Windows용 Ollama 설치"""
        # Chocolatey 사용 시도
        try:
            result = subprocess.run(['choco', 'install', 'ollama', '-y'], 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                logger.success("✅ Chocolatey로 Ollama 설치 완료")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # 수동 다운로드 및 설치 안내
        logger.info("💡 Windows에서 Ollama 수동 설치 방법:")
        logger.info("   1. https://ollama.ai/download 방문")
        logger.info("   2. Windows용 설치 파일 다운로드")
        logger.info("   3. 설치 후 이 스크립트를 다시 실행")
        
        try:
            response = input("Ollama를 설치했나요? (y/n): ").lower().strip()
            return response == 'y'
        except (KeyboardInterrupt, EOFError):
            return False
    
    def _install_ollama_macos(self):
        """macOS용 Ollama 설치"""
        # Homebrew 사용 시도
        try:
            result = subprocess.run(['brew', 'install', 'ollama'], 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                logger.success("✅ Homebrew로 Ollama 설치 완료")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # 수동 설치 안내
        logger.info("💡 macOS에서 Ollama 수동 설치 방법:")
        logger.info("   1. 터미널에서: curl -fsSL https://ollama.ai/install.sh | sh")
        logger.info("   2. 또는 https://ollama.ai/download 에서 앱 다운로드")
        
        try:
            response = input("Ollama를 설치했나요? (y/n): ").lower().strip()
            return response == 'y'
        except (KeyboardInterrupt, EOFError):
            return False
    
    def _install_ollama_linux(self):
        """Linux용 Ollama 설치"""
        try:
            # 공식 설치 스크립트 실행
            result = subprocess.run(['curl', '-fsSL', 'https://ollama.ai/install.sh'], 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                # 스크립트를 bash로 실행
                process = subprocess.run(['bash'], input=result.stdout, 
                                       text=True, timeout=300)
                if process.returncode == 0:
                    logger.success("✅ Linux에 Ollama 설치 완료")
                    return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            logger.error(f"자동 설치 실패: {e}")
        
        # 수동 설치 안내
        logger.info("💡 Linux에서 Ollama 수동 설치 방법:")
        logger.info("   터미널에서: curl -fsSL https://ollama.ai/install.sh | sh")
        
        try:
            response = input("Ollama를 설치했나요? (y/n): ").lower().strip()
            return response == 'y'
        except (KeyboardInterrupt, EOFError):
            return False
    
    def check_ollama_running(self):
        """Ollama 서비스가 실행 중인지 확인"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Ollama 서비스 실행 중")
                return True
        except requests.exceptions.RequestException:
            pass
        
        logger.warning("⚠️ Ollama 서비스가 실행되지 않음")
        return False
    
    def start_ollama_service(self):
        """Ollama 서비스 시작"""
        logger.info("🚀 Ollama 서비스 시작 중...")
        
        try:
            if self.platform == 'windows':
                # Windows에서 백그라운드로 ollama serve 실행
                subprocess.Popen(['ollama', 'serve'], 
                               creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                # macOS/Linux에서 백그라운드로 실행
                subprocess.Popen(['ollama', 'serve'], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
            
            # 서비스 시작 대기
            for i in range(30):  # 최대 30초 대기
                time.sleep(1)
                if self.check_ollama_running():
                    logger.success("✅ Ollama 서비스 시작 완료")
                    return True
                
            logger.error("❌ Ollama 서비스 시작 타임아웃")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ollama 서비스 시작 실패: {e}")
            return False
    
    def check_model_installed(self, model_name=None):
        """특정 모델이 설치되어 있는지 확인"""
        if model_name is None:
            model_name = self.model_name
            
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                for model in models:
                    if model_name in model.get('name', ''):
                        logger.info(f"✅ 모델 '{model_name}' 설치 확인")
                        return True
        except Exception as e:
            logger.error(f"모델 확인 중 오류: {e}")
        
        logger.warning(f"⚠️ 모델 '{model_name}'이 설치되지 않음")
        return False
    
    def install_model(self, model_name=None):
        """모델 다운로드 및 설치"""
        if model_name is None:
            model_name = self.model_name
            
        logger.info(f"📥 모델 '{model_name}' 다운로드 시작...")
        logger.info("⏳ 이 작업은 시간이 오래 걸릴 수 있습니다 (수 GB 다운로드)")
        
        try:
            # ollama pull 명령 실행
            process = subprocess.Popen(
                ['ollama', 'pull', model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 실시간 출력 표시
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            
            if process.returncode == 0:
                logger.success(f"✅ 모델 '{model_name}' 설치 완료")
                return True
            else:
                logger.error(f"❌ 모델 '{model_name}' 설치 실패")
                return False
                
        except Exception as e:
            logger.error(f"❌ 모델 설치 중 오류: {e}")
            return False
    
    def test_model(self, model_name=None):
        """모델 테스트 실행"""
        if model_name is None:
            model_name = self.model_name
            
        logger.info(f"🧪 모델 '{model_name}' 테스트 중...")
        
        test_prompt = "Hello! Please respond with just 'OK' to confirm you're working."
        
        try:
            payload = {
                "model": model_name,
                "prompt": test_prompt,
                "stream": False
            }
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                model_response = result.get('response', '').strip()
                logger.info(f"📝 모델 응답: {model_response}")
                logger.success(f"✅ 모델 '{model_name}' 테스트 성공")
                return True
            else:
                logger.error(f"❌ 모델 테스트 실패: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 모델 테스트 중 오류: {e}")
            return False
    
    def setup_complete_environment(self):
        """전체 Ollama/Llama3 환경 설정"""
        logger.info("🔧 Ollama/Llama3 환경 설정 시작")
        
        # 1. Ollama 설치 확인
        if not self.check_ollama_installed():
            if not self.install_ollama():
                logger.error("❌ Ollama 설치 실패")
                return False
        
        # 2. 서비스 실행 확인
        if not self.check_ollama_running():
            if not self.start_ollama_service():
                logger.error("❌ Ollama 서비스 시작 실패")
                return False
        
        # 3. 모델 설치 확인
        if not self.check_model_installed():
            if not self.install_model():
                logger.error("❌ 모델 설치 실패")
                return False
        
        # 4. 모델 테스트
        if not self.test_model():
            logger.error("❌ 모델 테스트 실패")
            return False
        
        logger.success("🎉 Ollama/Llama3 환경 설정 완료!")
        return True


def check_env_local():
    """환경 변수에서 LLM_PROVIDER가 local인지 확인"""
    try:
        # .env 파일 읽기
        env_file = Path('.env')
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # LLM_PROVIDER 찾기
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('LLM_PROVIDER='):
                    value = line.split('=', 1)[1].strip().strip('"').strip("'")
                    return value.lower() == 'local'
        
        # 시스템 환경변수 확인
        return os.getenv('LLM_PROVIDER', '').lower() == 'local'
        
    except Exception as e:
        logger.error(f"환경 설정 확인 중 오류: {e}")
        return False


def main():
    """메인 실행 함수"""
    logger.info("🤖 Ollama/Llama3 설정 유틸리티")
    
    # 환경 설정 확인
    if not check_env_local():
        logger.info("💡 LLM_PROVIDER가 'local'이 아니므로 Ollama 설정을 건너뜁니다")
        return True
    
    # Ollama 환경 설정
    manager = OllamaManager()
    return manager.setup_complete_environment()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

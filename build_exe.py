#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyInstaller를 사용한 exe 파일 빌드 스크립트
"""

import os
import shutil
from pathlib import Path
import subprocess
import sys

def clean_build_directories():
    """이전 빌드 결과물 정리"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"🗑️ 제거됨: {dir_name}")
    
    # spec 파일 제거
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()
        print(f"🗑️ 제거됨: {spec_file}")

def build_executable():
    """실행 파일 빌드"""
    print("🔨 실행 파일 빌드 시작...")
    
    try:
        # PyInstaller 실행
        result = subprocess.run([
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--onefile',
            '--name=WebCrawler',
            '--console',
            '--add-data=config;config',
            '--add-data=src;src',
            '--hidden-import=src.agent.autonomous_agent',
            '--hidden-import=src.crawler.hybrid_extractor',
            '--hidden-import=src.llm.base_client',
            '--hidden-import=src.llm.gemini_client',
            '--hidden-import=src.llm.local_client',
            '--hidden-import=src.models.packet',
            '--hidden-import=src.utils.deployment_utils',
            '--hidden-import=src.utils.link_filter',
            'run_agent.py'
        ], check=True, capture_output=True, text=True)
        
        print("✅ 빌드 성공!")
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 빌드 실패: {e}")
        print("stderr:", e.stderr)
        print("stdout:", e.stdout)
        return False
    
    return True

def create_deployment_structure():
    """배포용 폴더 구조 생성"""
    deployment_dir = Path("deployment")
    
    if deployment_dir.exists():
        shutil.rmtree(deployment_dir)
    
    deployment_dir.mkdir()
    
    # exe 파일 복사
    exe_file = Path("dist/WebCrawler.exe")
    if exe_file.exists():
        shutil.copy2(exe_file, deployment_dir / "WebCrawler.exe")
        print(f"📦 실행파일 복사: {deployment_dir / 'WebCrawler.exe'}")
    
    # README 파일 생성
    readme_content = """# WebCrawler 사용법

## 🚀 시작하기

1. **WebCrawler.exe** 파일을 실행합니다.
2. 첫 실행 시 필요한 폴더들이 자동으로 생성됩니다:
   - `input/` : 크롤링 대상 정보가 담긴 엑셀 파일을 넣는 폴더
   - `output/` : 크롤링 결과가 저장되는 폴더 
   - `logs/` : 실행 로그가 저장되는 폴더
   - `config/` : 설정 파일이 저장되는 폴더

## 📄 입력 파일 형식

`input/` 폴더에 다음 형식의 엑셀 파일(.xlsx)을 넣어주세요:

| 기관/단체/회사 | 주요 내용 | 웹사이트 주소 |
|---------------|----------|-------------|
| 예시 회사 A | 회사 소개 및 주요 사업 분야 | https://example.com |
| 예시 기관 B | 기관 연혁 및 주요 업무 | https://example2.com |

## 📁 결과 확인

- 크롤링 결과는 `output/날짜/도메인명/` 폴더에 JSON 파일로 저장됩니다.
- 실행 로그는 `logs/날짜/` 폴더에서 확인할 수 있습니다.

## ⚠️ 주의사항

- 인터넷 연결이 필요합니다.
- 크롤링 대상 사이트의 이용약관을 준수해주세요.
- 대용량 사이트의 경우 처리 시간이 오래 걸릴 수 있습니다.

## 🆘 문제 해결

- 실행 중 오류 발생 시 `logs/` 폴더의 로그 파일을 확인해주세요.
- 방화벽이나 백신 프로그램에서 차단되는 경우 예외 처리해주세요.
"""
    
    readme_path = deployment_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"📄 사용법 작성: {readme_path}")
    
    return deployment_dir

def main():
    """메인 빌드 프로세스"""
    print("🏗️ WebCrawler 배포 빌드 시작")
    print("-" * 50)
    
    # 1. 기존 빌드 결과물 정리
    print("1️⃣ 이전 빌드 결과물 정리...")
    clean_build_directories()
    print()
    
    # 2. 실행 파일 빌드
    print("2️⃣ 실행 파일 빌드...")
    success = build_executable()
    if not success:
        print("❌ 빌드에 실패했습니다.")
        return
    print()
    
    # 3. 배포용 폴더 구조 생성
    print("3️⃣ 배포 패키지 생성...")
    deployment_dir = create_deployment_structure()
    print()
    
    # 4. 완료 메시지
    print("✅ 배포 빌드 완료!")
    print(f"📦 배포 패키지 위치: {deployment_dir.absolute()}")
    print()
    print("🎯 배포 방법:")
    print(f"   1. {deployment_dir} 폴더를 원하는 위치에 복사")
    print("   2. WebCrawler.exe 실행")
    print("   3. input 폴더에 크롤링 대상 엑셀 파일 추가")
    print("   4. 프로그램 실행하여 크롤링 시작")

if __name__ == "__main__":
    main()

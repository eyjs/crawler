@echo off
chcp 65001 >nul
echo ========================================
echo 🚀 LLM 크롤러 설치 스크립트
echo ========================================

echo.
echo 📍 현재 위치: %CD%
echo.

echo 💡 참고: Visual C++ 빌드 도구가 필요한 경우
echo    완전 자동 설치를 원하면: install_full.ps1 실행 (관리자 권한)
echo.

echo 1. 시스템 요구사항 확인...

REM Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되지 않았습니다
    echo 💡 https://www.python.org/downloads/ 에서 설치하세요
    pause
    exit /b 1
) else (
    echo ✅ Python 설치 확인
    python --version
)

REM Chocolatey 설치 확인 (선택사항)
choco --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Chocolatey가 설치되지 않았습니다 (선택사항)
    echo 💡 aiohttp 설치를 위해 권장됩니다
) else (
    echo ✅ Chocolatey 설치 확인
    choco --version
)

echo.
echo 2. 가상환경 설정...
if exist ".venv" (
    echo ✅ .venv 폴더가 이미 존재합니다
) else (
    echo 📦 새 가상환경 생성...
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ 가상환경 생성 실패
        pause
        exit /b 1
    )
    echo ✅ 가상환경 생성 완료
)

echo.
echo 3. 가상환경 활성화...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 가상환경 활성화 실패
    pause
    exit /b 1
)
echo ✅ 가상환경 활성화됨

echo.
echo 4. pip 업그레이드...
python -m pip install --upgrade pip

echo.
echo 5. 핵심 패키지 설치...
echo 📦 google-generativeai 설치...
pip install google-generativeai==0.7.2

echo 📦 python-dotenv 설치...
pip install python-dotenv==1.0.1

echo 📦 loguru 설치...
pip install loguru==0.7.2

echo 📦 beautifulsoup4 설치...
pip install beautifulsoup4==4.12.3

echo 📦 requests 설치...
pip install requests==2.31.0

echo ✅ 핵심 패키지 설치 완료!

echo.
echo 6. aiohttp 설치 시도...
echo 💡 Visual C++ 빌드 도구가 필요할 수 있습니다
pip install aiohttp==3.9.5
if errorlevel 1 (
    echo ⚠️ aiohttp 설치 실패!
    echo.
    echo 💡 해결방법:
    echo    1. 완전 자동 설치: PowerShell에서 install_full.ps1 실행 (관리자 권한)
    echo    2. 수동 설치: Visual Studio Build Tools 설치
    echo       https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo    3. 하이브리드 크롤러 사용 (aiohttp 없이도 동작)
    echo.
) else (
    echo ✅ aiohttp 설치 성공!
)

echo.
echo 7. 설정 확인...
if not exist ".env" (
    echo ❌ .env 파일이 없습니다
    echo 💡 .env 파일에 GEMINI_API_KEY를 설정해야 합니다
) else (
    echo ✅ .env 파일 존재 확인
)

echo.
echo 8. 모듈 로드 테스트...
python -c "from src.llm.gemini_client import gemini_client; print('✅ 모듈 로드 성공')"
if errorlevel 1 (
    echo ⚠️ 모듈 로드에 문제가 있을 수 있습니다
) else (
    echo ✅ 모든 모듈 정상 로드
)

echo.
echo ========================================
echo 🎉 설치 완료!
echo ========================================
echo.
echo ✅ 기본 설치가 완료되었습니다!
echo.
echo 📋 다음 단계:
echo    1. .env 파일에 GEMINI_API_KEY 설정
echo    2. python quick_demo.py 실행하여 테스트
echo    3. python test_with_save.py 실행하여 전체 테스트
echo.
echo 💡 고급 기능:
echo    - 완전 자동 설치: install_full.ps1 (PowerShell, 관리자 권한)
echo    - 시스템 요구사항: SYSTEM_REQUIREMENTS.md 참고
echo.

pause
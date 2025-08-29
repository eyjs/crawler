@echo off
setlocal EnableDelayedExpansion

title Crawler Project Setup

echo =================================================================
echo.
echo     🚀 LLM Crawler Agent - 프로젝트 환경 구성
echo.
echo =================================================================
echo.

:: 1. 가상환경 생성
if not exist .venv (
    echo [1/4] '.venv' 가상환경을 생성합니다...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo ❌ [오류] 가상환경 생성에 실패했습니다. Python이 설치되어 있는지 확인하세요.
        pause
        exit /b 1
    )
    echo    ✅ 완료.
) else (
    echo [1/4] '.venv' 가상환경이 이미 존재합니다.
)
echo.

:: 2. .env 파일 설정
if not exist .env (
    echo [2/4] '.env' 설정 파일을 생성합니다...
    if not exist .env.sample (
        echo ❌ [오류] '.env.sample' 파일이 없습니다.
        pause
        exit /b 1
    )
    copy .env.sample .env > nul
    echo    ✅ '.env.sample'을 복사하여 '.env' 파일을 생성했습니다.
    echo.
    echo    ===============================[ 중요 ]================================
    echo    잠시 후 메모장으로 '.env' 파일이 열립니다.
    echo.
    echo    📝 다음 중 하나를 선택하여 설정하세요:
    echo       - 로컬 LLM 사용: LLM_PROVIDER="local" (무료, 인터넷 불필요)
    echo       - Gemini API 사용: LLM_PROVIDER="gemini" + API 키 설정
    echo.
    echo    설정 후 메모장을 닫고 여기서 Enter 키를 눌러 계속 진행하세요.
    echo    =======================================================================
    echo.

    start "" /wait notepad .env

) else (
    echo [2/4] '.env' 설정 파일이 이미 존재합니다.
)
echo.

:: 3. 필수 패키지 설치
echo [3/4] 필수 패키지를 가상환경에 설치합니다...
call .venv\Scripts\activate.bat
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ [오류] 패키지 설치에 실패했습니다.
    pause
    exit /b 1
)
echo    ✅ 완료.
echo.

:: 4. 로컬 LLM (Ollama/Llama3) 환경 확인
echo [4/4] 로컬 LLM 환경을 확인합니다...

:: .env 파일에서 LLM_PROVIDER 값 읽기
set "LLM_PROVIDER="
for /f "tokens=2 delims==" %%a in ('findstr /b "LLM_PROVIDER" .env 2^>nul') do (
    set "LLM_PROVIDER=%%a"
)

:: 따옴표 제거
set "LLM_PROVIDER=%LLM_PROVIDER:"=%"
set "LLM_PROVIDER=%LLM_PROVIDER:'=%"

if /i "%LLM_PROVIDER%"=="local" (
    echo    🤖 로컬 LLM 모드가 선택되었습니다. Ollama/Llama3 환경을 설정합니다...
    
    :: Python을 사용하여 Ollama 설정 스크립트 실행
    python -c "import sys; sys.path.append('.'); from src.utils.ollama_manager import main; success = main(); sys.exit(0 if success else 1)"
    
    if %errorlevel% neq 0 (
        echo    ⚠️ Ollama 자동 설정에 실패했습니다.
        echo    💡 수동 설치 방법:
        echo       1. https://ollama.ai/download 에서 Ollama 다운로드
        echo       2. 설치 후 'ollama pull llama3' 명령 실행
        echo       3. 프로그램 실행 시 자동으로 Ollama 서비스 시작됨
        echo.
    ) else (
        echo    ✅ Ollama/Llama3 환경 설정 완료!
    )
) else (
    echo    🌐 Gemini API 모드가 선택되었습니다. (Ollama 설정 건너뜀)
)
echo.

echo =================================================================
echo.
echo     ✅ 프로젝트 환경 구성이 완료되었습니다!
echo.
echo =================================================================
echo.
echo 📋 다음 단계:
if /i "%LLM_PROVIDER%"=="local" (
    echo    1. 가상환경 활성화: .venv\Scripts\activate.bat
    echo    2. 로컬 LLM 테스트: python -c "import ollama; print('OK')"
    echo    3. 에이전트 실행: python run_agent.py
) else (
    echo    1. 가상환경 활성화: .venv\Scripts\activate.bat
    echo    2. .env 파일에서 GEMINI_API_KEY 확인
    echo    3. 에이전트 실행: python run_agent.py
)
echo.
echo 🚀 지능형 크롤링을 시작할 준비가 되었습니다!
echo.
pause
exit /b 0

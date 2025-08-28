@echo off
setlocal
title Crawler Project Setup

echo =================================================================
echo.
echo     LLM Crawler Agent - 프로젝트 환경 구성
echo.
echo =================================================================
echo.

:: 1. 가상환경 생성
if not exist .venv (
    echo [1/3] '.venv' 가상환경을 생성합니다...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [오류] 가상환경 생성에 실패했습니다. Python이 설치되어 있는지 확인하세요.
        pause
        exit /b 1
    )
    echo    -> 완료.
) else (
    echo [1/3] '.venv' 가상환경이 이미 존재합니다.
)
echo.

:: 2. .env 파일 설정
if not exist .env (
    echo [2/3] '.env' 설정 파일을 생성합니다...
    if not exist .env.sample (
        echo [오류] '.env.sample' 파일이 없습니다.
        pause
        exit /b 1
    )
    copy .env.sample .env > nul
    echo    -> '.env.sample'을 복사하여 '.env' 파일을 생성했습니다.
    echo.
    echo    ===============================[ 중요 ]================================
    echo    잠시 후 메모장으로 '.env' 파일이 열립니다.
    echo    GEMINI_API_KEY 값을 당신의 API 키로 수정하고 저장한 뒤,
    echo    메모장을 닫고 여기서 Enter 키를 눌러 계속 진행하세요.
    echo    =======================================================================
    echo.

    start "" /wait notepad .env

) else (
    echo [2/3] '.env' 설정 파일이 이미 존재합니다.
)
echo.

:: 3. 필수 패키지 설치
echo [3/3] 필수 패키지를 가상환경에 설치합니다...
call .venv\Scripts\activate.bat
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [오류] 패키지 설치에 실패했습니다.
    pause
    exit /b 1
)
echo    -> 완료.
echo.
echo.
echo =================================================================
echo.
echo     V 프로젝트 환경 구성이 완료되었습니다!
echo.
echo =================================================================
echo.
pause
exit /b 0
@echo off
setlocal EnableDelayedExpansion
:: Windows 콘솔 한글 출력 설정
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

title LLM Crawler Agent - Master Launcher

echo ================================================================
echo.
echo     🚀 LLM Crawler Agent - 통합 실행 시스템
echo.
echo ================================================================
echo.

:: 현재 디렉토리 확인
if not exist "run_agent.py" (
    echo ❌ run_agent.py 파일을 찾을 수 없습니다.
    echo 💡 크롤러 프로젝트 루트 디렉토리에서 실행해주세요.
    echo.
    pause
    exit /b 1
)

:: 1단계: 환경 구성 확인
echo [1/3] 환경 구성 상태를 확인합니다...
echo.

if not exist ".venv" (
    echo ⚠️ 가상환경이 구성되지 않았습니다.
    echo 💡 환경 구성을 진행하시겠습니까? (y/n)
    set /p setup_env="입력: "
    
    if /i "!setup_env!"=="y" (
        echo.
        echo 📦 환경 구성을 시작합니다...
        call setup.bat
        
        if !errorlevel! neq 0 (
            echo ❌ 환경 구성에 실패했습니다.
            pause
            exit /b 1
        )
    ) else (
        echo 💡 먼저 setup.bat을 실행하여 환경을 구성해주세요.
        pause
        exit /b 1
    )
)

:: 가상환경 활성화
echo 🔄 가상환경 활성화 중...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ 가상환경 활성화에 실패했습니다.
    pause
    exit /b 1
)

echo ✅ 환경 구성 완료
echo.

:: 2단계: 시스템 준비 상태 점검
echo [2/3] 시스템 준비 상태를 점검합니다...
echo.

python system_ready_check.py
set "check_result=!errorlevel!"

echo.
if !check_result! equ 0 (
    echo ✅ 시스템 점검 완료 - 모든 구성이 정상입니다.
) else (
    echo ⚠️ 시스템 점검에서 문제가 발견되었습니다.
    echo 💡 계속 진행하시겠습니까? (y/n)
    set /p continue_anyway="입력: "
    
    if /i not "!continue_anyway!"=="y" (
        echo 💡 문제를 해결한 후 다시 실행해주세요.
        pause
        exit /b 1
    )
)

echo.

:: 3단계: 크롤러 실행
echo [3/3] LLM Crawler Agent를 실행합니다...
echo.

:: 입력 파일 확인 및 샘플 생성 옵션
set "xlsx_found=0"
if exist "input\*.xlsx" set "xlsx_found=1"

if !xlsx_found! equ 0 (
    echo ⚠️ input 폴더에 Excel 파일(.xlsx)이 없습니다.
    echo.
    echo 💡 샘플 파일을 생성하시겠습니까? (y/n)
    set /p create_sample="입력: "
    
    if /i "!create_sample!"=="y" (
        echo 📄 샘플 파일 생성 중...
        python create_sample.py
        if !errorlevel! neq 0 (
            echo ❌ 샘플 파일 생성에 실패했습니다.
            pause
            exit /b 1
        )
        echo ✅ 샘플 파일이 생성되었습니다.
        echo 💡 input/test_crawling.xlsx 파일을 수정한 후 다시 실행해주세요.
        echo.
        pause
        exit /b 0
    ) else (
        echo 💡 input 폴더에 크롤링할 사이트 정보가 담긴 Excel 파일을 넣어주세요.
        echo.
        pause
        exit /b 1
    )
)

:: 크롤러 실행
echo 🚀 크롤링을 시작합니다...
echo.

python run_agent.py
set "crawler_result=!errorlevel!"

:: 결과 처리
echo.
echo ================================================================
if !crawler_result! equ 0 (
    echo.
    echo ✅ 크롤링이 성공적으로 완료되었습니다!
    echo.
    echo 📁 결과 확인:
    echo    - output/ 폴더에 크롤링 결과 저장
    echo    - logs/ 폴더에 상세 로그 저장
    echo.
    echo 💡 결과 폴더를 열어보시겠습니까? (y/n)
    set /p open_results="입력: "
    
    if /i "!open_results!"=="y" (
        explorer output
    )
) else (
    echo.
    echo ❌ 크롤링 중 오류가 발생했습니다.
    echo.
    echo 🔍 문제 해결:
    echo    1. logs/ 폴더의 로그 파일을 확인
    echo    2. .env 파일의 설정 확인
    echo    3. 인터넷 연결 상태 확인
    echo.
)

echo ================================================================
echo.
echo 👋 LLM Crawler Agent 종료
pause

@echo off
setlocal EnableDelayedExpansion


title LLM Crawler Agent

echo ================================================================
echo.
echo     🚀 LLM Crawler Agent 실행
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

:: 가상환경 확인
if not exist ".venv" (
    echo ❌ 가상환경을 찾을 수 없습니다.
    echo 💡 먼저 setup.bat을 실행하여 환경을 구성해주세요.
    echo.
    pause
    exit /b 1
)

:: 가상환경 활성화
echo 🔄 가상환경 활성화 중...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ 가상환경 활성화에 실패했습니다.
    pause
    exit /b 1
)

:: 입력 파일 확인
if not exist "input" mkdir input
if not exist "output" mkdir output
if not exist "logs" mkdir logs

:: 입력 파일 존재 확인
set "xlsx_found=0"
for %%f in (input\*.xlsx) do (
    set "xlsx_found=1"
    goto :found_xlsx
)

:found_xlsx
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
    ) else (
        echo 💡 input 폴더에 크롤링할 사이트 정보가 담긴 Excel 파일을 넣어주세요.
        echo.
        pause
        exit /b 1
    )
)

:: 크롤러 실행
echo.
echo 🚀 LLM Crawler Agent 시작...
echo.
python run_agent.py

:: 결과 확인
if %errorlevel% equ 0 (
    echo.
    echo ✅ 크롤링이 완료되었습니다!
    echo 📁 결과는 output 폴더에서 확인하세요.
) else (
    echo.
    echo ❌ 크롤링 중 오류가 발생했습니다.
    echo 📋 logs 폴더의 로그 파일을 확인해주세요.
)

echo.
echo 👋 LLM Crawler Agent 종료
pause

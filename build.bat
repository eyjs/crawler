@echo off
chcp 65001 > nul
title WebCrawler 배포 빌드

echo.
echo ==========================================
echo    WebCrawler 배포 빌드 스크립트
echo ==========================================
echo.

REM 가상환경 활성화 확인
if exist ".venv\Scripts\activate.bat" (
    echo 🔄 가상환경 활성화 중...
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️ 가상환경을 찾을 수 없습니다. 전역 Python을 사용합니다.
)

REM Python 및 필요 패키지 확인
echo.
echo 📋 환경 검사 중...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python이 설치되어 있지 않습니다.
    pause
    exit /b 1
)

REM PyInstaller 설치 확인
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo 📦 PyInstaller 설치 중...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo ❌ PyInstaller 설치에 실패했습니다.
        pause
        exit /b 1
    )
)

REM deployment_utils.py가 올바른 위치에 있는지 확인
if not exist "src\utils\deployment_utils.py" (
    echo ❌ deployment_utils.py 파일이 없습니다.
    echo    src\utils\deployment_utils.py 파일을 생성해주세요.
    pause
    exit /b 1
)

REM 빌드 실행
echo.
echo 🔨 배포 빌드 시작...
python build_exe.py

if %errorlevel% equ 0 (
    echo.
    echo ✅ 빌드가 성공적으로 완료되었습니다!
    echo 📁 deployment 폴더를 확인해주세요.
    echo.
    
    REM deployment 폴더 열기 (선택사항)
    set /p choice="배포 폴더를 열겠습니까? (y/n): "
    if /i "%choice%"=="y" (
        start explorer deployment
    )
) else (
    echo.
    echo ❌ 빌드에 실패했습니다.
    echo 로그를 확인하여 문제를 해결해주세요.
)

echo.
echo 작업이 완료되었습니다.
pause

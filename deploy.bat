@echo off
chcp 65001 > nul
setlocal

:: --- 배치 파일 창 제목 설정 ---
title Git Auto Commit & Push

:: --- 현재 브랜치 이름 가져오기 ---
echo.
echo [1/5] 현재 브랜치 정보를 확인합니다...
for /f "tokens=*" %%g in ('git rev-parse --abbrev-ref HEAD') do (set current_branch=%%g)

if not defined current_branch (
    echo.
    echo [오류] Git 브랜치 정보를 찾을 수 없습니다.
    echo Git 저장소 폴더에서 실행했는지 확인하세요.
    pause
    exit /b
)

echo    -> 현재 브랜치: %current_branch%
echo.

:: --- 사용자에게 커밋 메시지 입력받기 ---
echo [2/5] 커밋 메시지를 입력하세요. (입력하지 않으면 자동 메시지가 사용됩니다)
set /p user_message=" -> 메시지: "

:: --- 커밋 메시지 설정 (사용자 입력이 없으면 자동 생성) ---
if "%user_message%"=="" (
    set "commit_message=Automated commit at %date% %time%"
    echo    -> 자동 메시지가 생성되었습니다: %commit_message%
) else (
    set "commit_message=%user_message%"
    echo    -> 입력된 메시지를 사용합니다: %commit_message%
)
echo.

:: --- Git 명령어 실행 ---
echo [3/5] 모든 변경 사항을 Staging 합니다 (git add .)...
git add .
if %errorlevel% neq 0 (
    echo [오류] 'git add' 실행 중 오류가 발생했습니다.
    pause
    exit /b
)
echo    -> 완료.
echo.

echo [4/5] 변경 사항을 커밋합니다...
git commit -m "%commit_message%"
if %errorlevel% neq 0 (
    echo [오류] 'git commit' 실행 중 오류가 발생했습니다.
    echo 커밋할 변경 사항이 있는지 확인하세요.
    pause
    exit /b
)
echo    -> 완료.
echo.

echo [5/5] 원격 저장소(%current_branch% 브랜치)로 푸시합니다...
git push origin %current_branch%
if %errorlevel% neq 0 (
    echo [오류] 'git push' 실행 중 오류가 발생했습니다.
    echo 원격 저장소 연결 및 권한을 확인하세요.
    pause
    exit /b
)
echo.
echo.

echo ======================================================
echo  V 성공적으로 커밋 및 푸시가 완료되었습니다.
echo ======================================================

echo.
pause
endlocal
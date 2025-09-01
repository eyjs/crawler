@echo off
chcp 65001
git config core.autocrlf true
REM GitHub Pages 배포 스크립트 (Windows)
REM master의 최신 내용으로 gh-pages를 완전히 덮어씌움

REM master 브랜치로 전환 및 최신화
echo Switching to master branch...
git checkout master

REM 변경사항 자동 커밋
echo Committing local changes on master...
git add .
git commit -m "Auto-deploy commit" || echo No changes to commit

REM master 브랜치 푸시
echo Pushing changes to origin/master...
git push origin master

REM gh-pages 브랜치 존재 여부 확인
echo Checking if gh-pages branch exists...
git rev-parse --verify gh-pages >nul 2>&1
IF ERRORLEVEL 1 (
    echo gh-pages branch does not exist. Creating new gh-pages branch...
    git checkout -b gh-pages
    git push origin gh-pages
) ELSE (
    echo gh-pages branch exists. Switching...
    git checkout gh-pages
)

REM master 브랜치 내용으로 강제 덮어쓰기
echo Resetting gh-pages to match master...
git reset --hard master

REM gh-pages 브랜치 강제 푸시 (이력 덮어쓰기)
echo Pushing updates to gh-pages...
git push origin gh-pages --force

REM 다시 master으로 돌아가기
git checkout master

echo Deployment to GitHub Pages complete! gh-pages now matches master.
pause
# LLM Crawler Complete Auto Installation Script
# Run as Administrator!



param(
    [switch]$SkipChocolatey,
    [switch]$SkipBuildTools,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
🚀 LLM Crawler Complete Auto Installation Script

Usage:
  .\install_full.ps1                # Full automatic installation
  .\install_full.ps1 -SkipChocolatey    # Skip Chocolatey installation
  .\install_full.ps1 -SkipBuildTools    # Skip build tools installation
  .\install_full.ps1 -Help              # Show help
"@
    exit 0
}

Write-Host "=" * 60 -ForegroundColor Green
Write-Host "🚀 LLM Crawler Complete Auto Installation Started" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

# Check Administrator privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ Error: Administrator privileges required!" -ForegroundColor Red
    Write-Host "💡 Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host "✅ Administrator privileges confirmed" -ForegroundColor Green

# --- 1. System Dependencies (Chocolatey, Build Tools, Python) ---
Write-Host "`n[1/2] 시스템 의존성(Chocolatey, Build Tools)을 확인 및 설치합니다..." -ForegroundColor Cyan

# 1a. Install Chocolatey
if (-not $SkipChocolatey) {
    Write-Host "`n📦 Checking Chocolatey installation..." -ForegroundColor Cyan
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Host "✅ Chocolatey is already installed" -ForegroundColor Green
    } else {
        Write-Host "📥 Installing Chocolatey..." -ForegroundColor Yellow
        try {
            Set-ExecutionPolicy Bypass -Scope Process -Force
            [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
            Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        } catch { Write-Host "❌ Chocolatey installation failed: $($_.Exception.Message)" -ForegroundColor Red }
    }
} else { Write-Host "⏭️ Chocolatey installation skipped" -ForegroundColor Yellow }

# 1b. Install Visual C++ Build Tools
if (-not $SkipBuildTools) {
    Write-Host "`n🔨 Installing Visual C++ Build Tools..." -ForegroundColor Cyan
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        try {
            choco install visualstudio2022buildtools --params "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended" -y
        } catch { Write-Host "⚠️ Build tools installation via Chocolatey failed" -ForegroundColor Yellow }
    } else { Write-Host "⚠️ Cannot auto-install build tools without Chocolatey" -ForegroundColor Yellow }
} else { Write-Host "⏭️ Build tools installation skipped" -ForegroundColor Yellow }

# 1c. Install Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python is not installed" -ForegroundColor Red
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Host "📥 Installing Python via Chocolatey..." -ForegroundColor Yellow
        choco install python -y
    } else {
        Write-Host "💡 Please install Python manually: https://www.python.org/downloads/" -ForegroundColor Yellow
        pause
        exit 1
    }
}


# --- 2. Project Environment Setup (Calling setup.bat) ---
Write-Host "`n[2/2] 프로젝트 환경 구성을 위해 setup.bat을 호출합니다..." -ForegroundColor Cyan

if (-not (Test-Path "setup.bat")) {
    Write-Host "❌ Critical Error: 'setup.bat' file not found!" -ForegroundColor Red
    pause
    exit 1
}

try {
    # setup.bat을 실행하고 작업이 끝날 때까지 기다립니다.
    $process = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "setup.bat" -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        throw "setup.bat 스크립트 실행 중 오류가 발생했습니다."
    }
    Write-Host "✅ setup.bat 실행 완료." -ForegroundColor Green
} catch {
    Write-Host "❌ setup.bat 실행 실패: $($_.Exception.Message)" -ForegroundColor Red
    pause
    exit 1
}


# --- Completion Message ---
Write-Host "`n" + "=" * 60 -ForegroundColor Green
Write-Host "🎉 모든 설치 과정이 성공적으로 완료되었습니다!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "`n📋 다음 단계:" -ForegroundColor Yellow
Write-Host "1. 가상환경 활성화: .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "2. 에이전트 실행: python run_agent.py" -ForegroundColor White
Write-Host "`n🚀 지능형 크롤링을 시작할 준비가 되었습니다!" -ForegroundColor Green
pause
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

Notes:
- Must be run as Administrator
- Internet connection required
- Reboot may be required during installation
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

# 1. Install Chocolatey
if (-not $SkipChocolatey) {
    Write-Host "`n📦 Checking Chocolatey installation..." -ForegroundColor Cyan
    
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Host "✅ Chocolatey is already installed" -ForegroundColor Green
        choco --version
    } else {
        Write-Host "📥 Installing Chocolatey..." -ForegroundColor Yellow
        try {
            Set-ExecutionPolicy Bypass -Scope Process -Force
            [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
            Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
            
            # Refresh PATH
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
            
            Write-Host "✅ Chocolatey installation completed" -ForegroundColor Green
        } catch {
            Write-Host "❌ Chocolatey installation failed: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "💡 Install manually or use -SkipChocolatey option" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "⏭️ Chocolatey installation skipped" -ForegroundColor Yellow
}

# 2. Install Visual C++ Build Tools
if (-not $SkipBuildTools) {
    Write-Host "`n🔨 Installing Visual C++ Build Tools..." -ForegroundColor Cyan
    
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        try {
            # Install Visual Studio Build Tools
            Write-Host "📥 Installing Visual Studio Build Tools (this may take a while)..." -ForegroundColor Yellow
            choco install visualstudio2022buildtools --params "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended" -y
            
            # Alternative simpler version
            if ($LASTEXITCODE -ne 0) {
                Write-Host "📥 Trying alternative build tools installation..." -ForegroundColor Yellow
                choco install visualcpp-build-tools -y
            }
            
            Write-Host "✅ Visual C++ Build Tools installation completed" -ForegroundColor Green
        } catch {
            Write-Host "⚠️ Build tools installation via Chocolatey failed" -ForegroundColor Yellow
            Write-Host "💡 Manual installation may be required:" -ForegroundColor Yellow
            Write-Host "   https://visualstudio.microsoft.com/visual-cpp-build-tools/" -ForegroundColor Cyan
        }
    } else {
        Write-Host "⚠️ Cannot auto-install build tools without Chocolatey" -ForegroundColor Yellow
        Write-Host "💡 Manual installation link: https://visualstudio.microsoft.com/visual-cpp-build-tools/" -ForegroundColor Cyan
    }
} else {
    Write-Host "⏭️ Build tools installation skipped" -ForegroundColor Yellow
}

# 3. Python Environment Setup
Write-Host "`n🐍 Setting up Python environment..." -ForegroundColor Cyan

# Check Python installation
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonVersion = python --version
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Python is not installed" -ForegroundColor Red
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Host "📥 Installing Python via Chocolatey..." -ForegroundColor Yellow
        choco install python -y
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        Write-Host "✅ Python installation completed" -ForegroundColor Green
    } else {
        Write-Host "💡 Please install Python manually: https://www.python.org/downloads/" -ForegroundColor Yellow
        pause
        exit 1
    }
}

# 4. Virtual Environment and Package Installation
Write-Host "`n📦 Installing Python packages..." -ForegroundColor Cyan

if (Test-Path ".venv") {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
} else {
    Write-Host "📁 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        pause
        exit 1
    }
}

# Activate virtual environment
Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
try {
    & ".\.venv\Scripts\Activate.ps1"
} catch {
    Write-Host "❌ Failed to activate virtual environment" -ForegroundColor Red
    pause
    exit 1
}

# Upgrade pip
Write-Host "⬆️ Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install essential packages
Write-Host "📦 Installing essential packages..." -ForegroundColor Yellow
$essentialPackages = @(
    "google-generativeai==0.7.2",
    "python-dotenv==1.0.1",
    "loguru==0.7.2",
    "beautifulsoup4==4.12.3",
    "requests==2.31.0"
)

foreach ($package in $essentialPackages) {
    Write-Host "   📥 Installing $package..." -ForegroundColor Blue
    pip install $package
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   ⚠️ Failed to install $package" -ForegroundColor Yellow
    }
}

# Try to install aiohttp separately
Write-Host "`n🔄 Attempting to install aiohttp..." -ForegroundColor Cyan
pip install aiohttp==3.9.5
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ aiohttp installation successful!" -ForegroundColor Green
} else {
    Write-Host "⚠️ aiohttp installation failed - build tools may be needed" -ForegroundColor Yellow
    Write-Host "💡 You can use the hybrid crawler (requests-based) which works without aiohttp" -ForegroundColor Yellow
}

# 5. Configuration Check
Write-Host "`n⚙️ Checking configuration..." -ForegroundColor Cyan

if (Test-Path ".env") {
    Write-Host "✅ .env file exists" -ForegroundColor Green
} else {
    Write-Host "⚠️ .env file not found" -ForegroundColor Yellow
    Write-Host "💡 You need to set GEMINI_API_KEY" -ForegroundColor Yellow
}

# 6. Test Installation
Write-Host "`n🧪 Testing installation..." -ForegroundColor Cyan
try {
    python -c "from src.llm.gemini_client import gemini_client; print('✅ Module loading successful')"
    Write-Host "✅ All modules load successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠️ There may be issues with module loading" -ForegroundColor Yellow
    Write-Host "💡 Check if .env file has GEMINI_API_KEY set" -ForegroundColor Yellow
}

# Completion Message
Write-Host "`n" + "=" * 60 -ForegroundColor Green
Write-Host "🎉 Installation Complete!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Set GEMINI_API_KEY in .env file" -ForegroundColor White
Write-Host "2. Run: python quick_demo.py" -ForegroundColor White
Write-Host "3. Run: python test_with_save.py" -ForegroundColor White

Write-Host "`n💡 Troubleshooting:" -ForegroundColor Yellow
Write-Host "- If aiohttp failed: Use hybrid crawler (works without aiohttp)" -ForegroundColor White
Write-Host "- For build tools issues: Install Visual Studio Build Tools manually" -ForegroundColor White
Write-Host "- Check logs above for any installation errors" -ForegroundColor White

Write-Host "`n🚀 Ready to start intelligent crawling!" -ForegroundColor Green
pause

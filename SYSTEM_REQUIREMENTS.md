# 시스템 요구사항

## Python 패키지 (requirements.txt로 설치)
- google-generativeai==0.7.2
- beautifulsoup4==4.12.3
- requests==2.31.0
- python-dotenv==1.0.1
- loguru==0.7.2
- aiohttp==3.9.5 (선택사항 - C++ 빌드 도구 필요)

## 시스템 의존성 (자동 설치 스크립트로 설치)

### Windows
- Microsoft Visual C++ 14.0 Build Tools (aiohttp 빌드용)
- Chocolatey (패키지 관리자)

### Chocolatey를 통한 설치
```bash
# Chocolatey 설치 (관리자 권한 필요)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Visual C++ 빌드 도구 설치
choco install visualcpp-build-tools -y

# Python 설치 (필요한 경우)
choco install python -y
```

### 수동 설치 링크
- Visual Studio Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Python: https://www.python.org/downloads/
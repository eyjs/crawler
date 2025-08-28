# 🚀 LLM 기반 지능형 크롤러 설치 가이드

## 📋 설치 옵션

### **방법 1: 완전 자동 설치 (권장)**
```powershell
# PowerShell을 관리자 권한으로 실행 후
.\install_full.ps1
```
- ✅ Chocolatey 자동 설치
- ✅ Visual C++ 빌드 도구 자동 설치  
- ✅ Python 패키지 자동 설치
- ✅ aiohttp 완벽 지원

### **방법 2: 기본 설치**
```bash
# 일반 사용자 권한으로 실행
setup.bat
```
- ✅ Python 패키지 설치
- ⚠️ Visual C++ 빌드 도구 수동 설치 필요 (aiohttp용)
- ✅ 하이브리드 크롤러는 정상 동작

### **방법 3: 수동 설치**
1. **Visual C++ 빌드 도구 설치**
   - https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - 또는 Chocolatey: `choco install visualcpp-build-tools -y`

2. **Python 환경 설정**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

## 🔧 시스템 요구사항

### **필수 요구사항**
- Windows 10/11
- Python 3.9 이상
- 인터넷 연결
- Google Gemini API 키

### **선택사항 (성능 향상)**
- Microsoft Visual C++ 14.0 Build Tools
- Chocolatey 패키지 관리자
- 관리자 권한 (자동 설치용)

## ⚙️ Chocolatey 설치 명령어

```powershell
# PowerShell 관리자 권한에서 실행
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Visual C++ 빌드 도구 설치
choco install visualcpp-build-tools -y

# Python 설치 (필요한 경우)
choco install python -y
```

## 🧪 설치 검증

설치 후 다음 명령어로 검증:

```bash
# 기본 모듈 테스트
python -c "from src.llm.gemini_client import gemini_client; print('✅ 성공')"

# aiohttp 설치 확인
python -c "import aiohttp; print('✅ aiohttp 사용 가능')"

# 빠른 데모 실행
python quick_demo.py
```

## ❌ 문제 해결

### **aiohttp 설치 실패**
```
error: Microsoft Visual C++ 14.0 or greater is required
```
**해결방법:**
1. `install_full.ps1` 실행 (관리자 권한)
2. 또는 Visual Studio Build Tools 수동 설치
3. 또는 하이브리드 크롤러 사용 (aiohttp 없이도 동작)

### **Chocolatey 설치 실패**
**해결방법:**
1. PowerShell을 관리자 권한으로 실행 확인
2. 방화벽/보안 소프트웨어 확인
3. 인터넷 연결 확인

### **Python 모듈 로드 실패**
**해결방법:**
1. 가상환경 활성화 확인: `.venv\Scripts\activate`
2. 패키지 재설치: `pip install -r requirements.txt`
3. Python 버전 확인: `python --version` (3.9 이상 필요)

## 📚 추가 자료

- **프로젝트 문서**: README.md
- **시스템 요구사항**: SYSTEM_REQUIREMENTS.md
- **API 문서**: https://docs.google.com/gemini
- **Visual Studio Build Tools**: https://visualstudio.microsoft.com/visual-cpp-build-tools/

---

💡 **팁**: 처음 설치하는 경우 `install_full.ps1`을 사용하는 것을 강력히 권장합니다!

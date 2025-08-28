# LLM 기반 지능형 크롤러

## 📖 프로젝트 개요
Google Gemini API를 활용하여 목표 지향적으로 웹을 탐색하고 관련성 높은 데이터만을 효율적으로 수집하는 지능형 크롤링 시스템입니다.

## ✨ 핵심 특징
- 🤖 **Gemini 기반 링크 평가**: 설정된 목표와 링크의 관련성을 지능적으로 판단
- 🎯 **목표 지향적 탐색**: 불필요한 페이지 방문을 최소화하고 효율성 극대화
- 📊 **실시간 성과 평가**: 각 페이지의 목표 달성도를 실시간으로 평가
- 🔄 **하이브리드 비동기 처리**: requests + asyncio로 고성능 병렬 크롤링
- 💾 **결과 저장**: JSON 및 텍스트 형태로 상세한 결과 저장

## 🛠️ 시스템 요구사항
- Python 3.9 이상
- Google Gemini API 키
- Windows (setup.bat 기준, Linux/Mac은 수동 설치)

## 🚀 설치 및 실행

### **방법 1: 완전 자동 설치 (권장)**
```powershell
# PowerShell을 관리자 권한으로 실행
cd D:\study\crawler
.\install_full.ps1
```
- ✅ Visual C++ 빌드 도구 자동 설치
- ✅ Chocolatey 자동 설치  
- ✅ Python 패키지 자동 설치
- ✅ aiohttp 완벽 지원

### **방법 2: 기본 설치**
```bash
# 일반 사용자 권한으로 실행
cd D:\study\crawler
setup.bat
```
- ✅ Python 패키지 설치
- ⚠️ Visual C++ 빌드 도구 수동 설치 필요
- ✅ 하이브리드 크롤러 정상 동작

### **방법 3: 수동 설치**
```bash
# 가상환경 생성
python -m venv .venv

# 가상환경 활성화 (Windows)
.venv\Scripts\activate

# 가상환경 활성화 (Linux/Mac)
source .venv/bin/activate

# 패키지 설치
pip install -r requirements.txt

# Visual C++ 빌드 도구 설치 (aiohttp용)
choco install visualcpp-build-tools -y
```

### **3. Gemini API 키 설정**
`.env` 파일을 열고 API 키를 설정하세요:
```
GEMINI_API_KEY=your_actual_api_key_here
```

## 🎯 사용법

### **빠른 데모 (1분)**
```bash
python quick_demo.py
```

### **전체 테스트 (결과 저장)**
```bash
python test_with_save.py
```

### **결과 확인**
```bash
python show_results.py
```

## 📂 프로젝트 구조
```
D:\study\crawler/
├── .env                    # 환경변수 설정
├── requirements.txt        # 패키지 의존성
├── setup.bat              # 자동 설치 스크립트
├── config/
│   └── settings.py        # 환경설정 관리
├── src/
│   ├── crawler/
│   │   └── hybrid_extractor.py  # 하이브리드 크롤러
│   └── llm/
│       └── gemini_client.py     # Gemini API 클라이언트
├── test_configs/          # 테스트 설정 파일들
│   ├── quick_test.json   # 빠른 테스트용
│   └── full_test.json    # 전체 테스트용
├── test_results/         # 테스트 결과 저장소
├── logs/                 # 로그 파일
├── quick_demo.py         # 1분 데모
├── test_with_save.py     # 결과 저장 테스트
└── show_results.py       # 결과 확인
```

## 🔧 설정 커스터마이징

### **테스트 사이트 변경**
`test_configs/quick_test.json` 파일을 수정하여 원하는 사이트를 테스트할 수 있습니다:

```json
{
  "test_cases": [
    {
      "name": "사용자 정의 테스트",
      "url": "https://example.com",
      "prompt": "원하는 키워드, 검색 목표"
    }
  ],
  "crawler_settings": {
    "max_pages": 3,
    "relevance_threshold": 0.5,
    "request_delay": 1.0,
    "timeout": 20
  }
}
```

### **환경변수 설정**
`.env` 파일에서 다양한 설정을 변경할 수 있습니다:
- `RELEVANCE_THRESHOLD`: 관련성 임계값 (0.0~1.0)
- `REQUEST_DELAY`: 요청 간 지연시간 (초)
- `PAGE_LOAD_TIMEOUT`: 페이지 로드 타임아웃 (초)

## 📊 결과 해석

테스트 실행 후 `test_results/` 폴더에서 다음을 확인할 수 있습니다:

- **상세 JSON 결과**: 모든 링크 평가 점수와 메타데이터
- **요약 텍스트 리포트**: 읽기 쉬운 형태의 결과 요약
- **관련성 높은 링크 목록**: 설정된 임계값 이상의 링크들

## 🔍 주요 기능

### **지능형 링크 평가**
- LLM이 각 링크의 관련성을 0.0~1.0 점수로 평가
- 컨텍스트 기반 판단 (링크 주변 텍스트 분석)
- 설정 가능한 관련성 임계값

### **효율적인 크롤링**
- 비동기 처리로 빠른 성능
- 중복 방문 방지
- 타임아웃 및 에러 핸들링

### **상세한 결과 저장**
- JSON 형태의 상세 데이터
- 텍스트 형태의 요약 리포트
- 타임스탬프 기반 파일 관리

## 🚨 주의사항

- Gemini API 키가 설정되어 있어야 합니다
- 과도한 요청으로 인한 API 제한에 주의하세요
- 대상 사이트의 robots.txt를 준수하세요

## 🤝 기여하기

이 프로젝트는 학습용으로 제작되었습니다. 개선 사항이나 버그 발견 시 이슈를 등록해 주세요.

## 📄 라이센스
MIT License

---

**🎉 Happy Crawling with AI!**

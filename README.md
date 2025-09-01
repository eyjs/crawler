# 🚀 LLM Crawler Agent

지능형 웹 크롤링 에이전트 - 로컬 LLM(Llama3) 또는 Gemini API를 사용한 자동 웹 크롤링 시스템

## 📋 실행 흐름

### 🎯 **통합 실행 (권장)**
```bash
# 한 번에 모든 것을 처리하는 마스터 스크립트
start_crawler.bat
```

### 🔧 **단계별 실행**

#### 1️⃣ **환경 구성** (처음 한 번만)
```bash
# 옵션 A: PowerShell 통합 설치 (관리자 권한 필요)
install_full.ps1

# 옵션 B: 기본 환경 구성
setup.bat
```

#### 2️⃣ **시스템 점검**
```bash
# 가상환경 활성화
.venv\Scripts\activate.bat

# 시스템 준비 상태 점검
python system_ready_check.py
```

#### 3️⃣ **크롤러 실행**
```bash
python run_agent.py
```

## 📁 프로젝트 구조

```
crawler/
├── 🎮 실행 스크립트
│   ├── start_crawler.bat          # 통합 실행 스크립트 (권장)
│   ├── install_full.ps1           # PowerShell 통합 설치
│   ├── setup.bat                  # 기본 환경 구성
│   └── run_crawler.bat           # 크롤러만 실행
│
├── 🛠️ 메인 프로그램
│   ├── run_agent.py               # 크롤러 메인 실행 파일
│   ├── system_ready_check.py      # 시스템 점검 도구
│   └── create_sample.py           # 샘플 파일 생성
│
├── 📂 소스 코드
│   ├── src/
│   │   ├── agent/                 # 크롤링 에이전트
│   │   ├── llm/                   # LLM 클라이언트
│   │   ├── crawler/               # 웹 크롤링 엔진
│   │   ├── models/                # 데이터 모델
│   │   └── utils/                 # 유틸리티
│   │       ├── deployment_utils.py # 배포 관리
│   │       └── ollama_manager.py   # Ollama 관리
│   │
├── 📄 설정 파일
│   ├── .env                       # 환경 변수 (setup.bat으로 생성)
│   ├── .env.sample               # 환경 변수 템플릿
│   ├── requirements.txt          # Python 패키지 목록
│   └── config/                   # 설정 파일들
│
├── 📁 작업 폴더 (자동 생성)
│   ├── input/                    # 크롤링 대상 Excel 파일
│   ├── output/                   # 크롤링 결과 JSON 파일
│   └── logs/                     # 실행 로그 파일
│
└── 🏗️ 배포 관련
    ├── build_exe.py              # exe 빌드 스크립트
    ├── build.bat                 # Windows 빌드
    └── deployment/               # 배포 패키지 (빌드 후 생성)
```

## ⚙️ 설정 방법

### LLM 선택

#### 🤖 **로컬 LLM 사용** (무료, 추천)
```env
LLM_PROVIDER="local"
LOCAL_LLM_MODEL="llama3"
```
- 장점: 무료, 인터넷 불필요, 개인정보 보안
- 단점: 초기 다운로드 용량 큼 (수GB), 더 느림

#### 🌐 **Gemini API 사용** (유료)
```env
LLM_PROVIDER="gemini"
GEMINI_API_KEY="your-api-key-here"
```
- 장점: 빠른 응답, 높은 정확도
- 단점: API 요금 발생, 인터넷 필요

## 📄 입력 파일 형식

`input/` 폴더에 다음 형식의 Excel 파일(.xlsx)을 넣어주세요:

| 기관/단체/회사 | 주요 내용 | 웹사이트 주소 |
|---------------|----------|-------------|
| 네이버 | 회사 소개 및 주요 서비스 | https://www.naver.com/about |
| 카카오 | 기업 정보 및 사업 분야 | https://www.kakaocorp.com/page/ |

## 📊 결과 확인

### 크롤링 결과
- **위치**: `output/날짜/도메인명/`
- **형식**: JSON 파일
- **내용**: 추출된 텍스트, 요약, 키워드

### 실행 로그
- **위치**: `logs/날짜/`
- **파일**: 
  - `system.log`: 전체 시스템 로그
  - `도메인명.log`: 사이트별 상세 로그

## 🔧 시스템 요구사항

### 기본 요구사항
- **OS**: Windows 10/11
- **RAM**: 최소 8GB (로컬 LLM 사용 시 16GB 권장)
- **저장공간**: 10GB 이상 여유 공간
- **네트워크**: 인터넷 연결 (모델 다운로드, 웹 크롤링용)

### 소프트웨어
- **Python**: 3.8 이상
- **Git**: 최신 버전 (소스 코드 다운로드용)

## 🚨 문제 해결

### 한글 깨짐 현상
- **해결책**: 제공된 실행 스크립트 사용 (`start_crawler.bat`)
- 모든 스크립트에 UTF-8 인코딩 설정 포함

### Ollama 설치 문제
```bash
# 수동 설치
# 1. https://ollama.ai/download 방문
# 2. Windows용 설치파일 다운로드
# 3. 설치 후 터미널에서 실행:
ollama pull llama3
```

### 권한 관련 오류
- **Windows**: 관리자 권한으로 실행
- **파일 접근**: 바이러스 백신 예외 처리 추가

### 네트워크 오류
- 방화벽 설정 확인
- 프록시 환경에서는 추가 설정 필요

## 📈 성능 최적화

### 로컬 LLM 성능 향상
- **GPU 사용**: NVIDIA GPU 있을 시 CUDA 가속
- **메모리**: 16GB 이상 RAM 권장
- **SSD**: 빠른 저장장치 사용

### 크롤링 성능 조정
```env
# .env 파일에서 설정 가능
MAX_PAGES_PER_SESSION=20     # 사이트별 최대 페이지 수
RELEVANCE_THRESHOLD=0.7      # 관련성 임계값
REQUEST_DELAY=1.5           # 요청 간 대기시간(초)
```

## 🔐 보안 고려사항

### API 키 보안
- `.env` 파일은 절대 공유하지 마세요
- Git에 커밋하지 마세요 (`.gitignore`에 포함됨)

### 크롤링 윤리
- 대상 사이트의 이용약관 준수
- robots.txt 파일 존중
- 적절한 요청 간격 유지

## 📞 지원 및 문의

### 로그 파일 위치
- `logs/날짜/system.log`: 전체 시스템 로그
- `logs/날짜/도메인.log`: 사이트별 로그

### 자주 발생하는 문제
1. **가상환경 오류**: `setup.bat` 재실행
2. **모델 다운로드 느림**: 네트워크 상태 확인
3. **크롤링 실패**: 대상 사이트 접근성 확인

---

## 🏃‍♂️ 빠른 시작

1. **프로젝트 다운로드**
   ```bash
   git clone [repository-url]
   cd crawler
   ```

2. **통합 실행**
   ```bash
   start_crawler.bat
   ```

3. **결과 확인**
   - `output/` 폴더에서 크롤링 결과 확인
   - `logs/` 폴더에서 실행 로그 확인

🎉 **이제 지능형 웹 크롤링을 시작할 준비가 완료되었습니다!**
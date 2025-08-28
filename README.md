# LLM 기반 지능형 크롤링 에이전트

## 📖 프로젝트 개요

이 프로젝트는 사용자가 정의한 목표(`instruction prompt`)에 따라 웹사이트를 자율적으로 탐색하고, LLM(거대 언어 모델)을 활용하여 관련성 높은 콘텐츠만을 지능적으로 수집, 요약, 구조화하는 데이터 처리 에이전트입니다.

## ✨ 핵심 특징

- **🤖 자율 탐색 에이전트**: 시작 URL과 목표만 주어지면, 관련성 높은 링크를 스스로 판단하여 탐색을 확장합니다.
- **🧠 교체 가능한 LLM 엔진**: `.env` 설정 변경만으로 고성능 **Google Gemini API**와 비용 없는 **로컬 LLM(Ollama/Llama3)**을 자유롭게 전환할 수 있습니다.
- **📄 지능형 콘텐츠 강화**: 수집된 웹페이지 본문에서 자동으로 **3줄 요약**과 **핵심 키워드**를 추출하여 데이터의 가치를 높입니다.
- **💰 비용 최적화**: 불필요한 링크(로그인, 채용 등)를 사전에 필터링하고, 한번 평가한 URL은 캐싱하여 LLM API 호출을 최소화합니다.
- **📦 표준 데이터 패킷**: 수집된 모든 데이터는 기획서에 명시된 표준 JSON 구조로 생성되어 `crawled_results` 폴더에 저장됩니다.
- **📜 상세 로깅**: 모든 탐색 과정은 사이트별 개별 로그 파일(`logs` 폴더)에 상세히 기록되어 추적이 용이합니다.

## 🚀 빠른 시작 가이드 (Quick Start)

이 프로젝트를 처음 실행하는 경우, 아래 단계를 순서대로 따라주세요.

### 1. 사전 요구사항

- **Python 3.9 이상**
- **Ollama (로컬 LLM 사용 시)**: 로컬 LLM(`LLM_PROVIDER="local"`)을 사용하려면 [Ollama](https://ollama.com)가 설치되어 있고, 터미널에서 `ollama run llama3` 명령이 한 번 이상 실행된 상태여야 합니다.

### 2. 프로젝트 클론

```bash
git clone [https://github.com/eyjs/crawler.git](https://github.com/eyjs/crawler.git)
cd crawler
```

### 3. 환경번수 설정

```bash
# Windows
copy .env.sample .env

# Linux / Mac
cp .env.sample .env
```

### 4. 필수 패키지 설치

```bash
# Windows
# setup.bat을 실행하면 가상환경 생성부터 패키지 설치까지 자동으로 진행됩니다.
setup.bat

# Linux / Mac (수동 설치)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5. 에이전트 실행

```bash
# 가상환경 활성화 (setup.bat을 사용하지 않은 경우)
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

# 에이전트 실행
python run_agent.py
```

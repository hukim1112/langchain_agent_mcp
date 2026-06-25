# 🕷️ LangChain agent - MCP 실습

> LangChain 에이전트 구축 및 MCP 서버 연동 실습

---

## 🔍 프로젝트 소개


---

## 🚀 시작하기 (환경 세팅)

Codespaces 또는 로컬 WSL2(우분투) 환경을 처음 열었다면, 터미널에서 다음 명령어를 실행하여 필요한 시스템 의존성 및 라이브러리를 설치하세요.

```bash
bash install.sh
```

설치 스크립트는 다음 작업을 수행합니다:
1. **시스템 패키지 설치**: PDF 처리 및 멀티모달 기능 작동을 위한 `poppler-utils` 설치
2. **필수 라이브러리 설치**: `requirements.txt`에 나열된 패키지 및 구글 드라이브 다운로더 `gdown` 설치

### 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 아래 키를 설정하세요. (`.env_template`을 복사해 사용하실 수 있습니다.)

> 에이전트가 정상적으로 웹 탐색을 수행하고 작동하게 하려면 **Tavily API 키**와 **LangSmith API 키**를 반드시 `.env` 파일에 기입해야 합니다.

```env
OPENAI_API_KEY="your-api-key"
GOOGLE_API_KEY="your-api-key"
TAVILY_API_KEY="your-tavily-api-key"   # 웹 검색(Tavily) 기능을 위해 반드시 입력해야 합니다.
```

### 🔍 LangSmith 트레이싱 설정 (권장)

**[LangSmith](https://smith.langchain.com)** 는 LangChain/LangGraph 에이전트의 실행 흐름을 시각적으로 추적하고 디버깅할 수 있는 공식 모니터링 플랫폼입니다.  
에이전트가 어떤 도구를 호출했는지, LLM에 어떤 프롬프트가 들어갔는지, 응답 시간과 토큰 비용은 얼마나 들었는지를 웹 UI에서 한눈에 확인하고 디버깅 시간을 크게 줄일 수 있습니다.

```env
LANGCHAIN_API_KEY="your-langsmith-key" # LangSmith 트레이싱 및 디버깅을 위해 입력해야 합니다.
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=AAWS  # 프로젝트 이름
```

---

## 🧭 커리큘럼 및 노트북 구조

학습 흐름은 점진적 빌드업(Step-by-step) 형태로 구성되어 있습니다.

```
notebooks/
├── 01_playwright_test_with_noVNC.ipynb # 🌐 Playwright 및 VNC 가상 화면 동작성 검증
├── 02_browser-use.ipynb                # 🕷️ browser-use의 동작 기본 원리 및 네이버 뉴스 실습
├── 03_The_Navigator.ipynb              # 🗺️ 웹 탐색 에이전트 (Navigator) 및 shared_browser 설계
├── 04_The_Coder.ipynb                  # 💻 자가 디버깅(Self-Healing)이 탑재된 Coder 에이전트 설계
└──  05_MultiAgent_Workflow.ipynb        # 🔗 Navigator + Coder 파이프라인 자동화 (StateGraph)
```

| 단계 | 노트북 | 핵심 학습 목표 |
|:---:|--------|-----------|
| **1** | `01_playwright_test_with_noVNC` | 가상 데스크톱 디스플레이 환경과 Playwright 정상 구동 테스트 |
| **2** | `02_browser-use` | AI 비전(Vision) 기술을 통한 웹 페이지 자율 탐색 및 브라우저 제어 |
| **3** | `03_The_Navigator` | Agent as Tool 패턴, 멀티턴 대화, shared browser 기반 브라우저 세션 유지 |
| **4** | `04_The_Coder` | 코드 자동 생성, Python subprocess 기반 자가 오류 디버깅 루프 |
| **5** | `05_MultiAgent_Workflow` | Navigator(구조 분석/검증) ➔ Coder(크롤러 구현/실행) 파이프라인 자동화 |

---

## 📂 프로젝트 구조

학습 코드(Jupyter Notebook)와 서빙 코드(fastapi/streamlit), 평가 코드(evaluator/tests)가 단일 저장소 하위로 완벽하게 병합된 **통합 아키텍처**입니다.

```
AAWS/
├── notebooks/              # 📗 핸즈온 실습 노트북 (01~05)
├── app/                    # 🧠 에이전트 시스템 코어 패키지
│   ├── agents/             #   ├── 에이전트 팩토리 (navigator, coder, supervisor)
│   ├── tools/              #   ├── 에이전트 도구 모음 (navigator, coder, supervisor_tools, common)
│   ├── prompts/            #   ├── 시스템 프롬프트 (모듈화)
│   ├── schemas.py          #   └── PageLayer, NavigatorBlueprint 등 스키마 정의
│   ├── evaluator.py        #   └── LLM-as-a-Judge 기반 시나리오 평가 엔진
│   ├── scenario_parser.py  #   └── 시나리오 마크다운 파서
│   ├── server.py           #   └── 에이전트 API 서빙 백엔드 (FastAPI)
│   ├── client.py           #   └── 터미널용 테스트 CLI 클라이언트
│   └── ui.py               #   └── 에이전트 실시간 채팅 프론트엔드 (Streamlit)
├── workflows/              # 🔗 시나리오 자동 실행을 위한 워크플로우 정의
├── tests/                  # 🧪 평가 자동화 및 러너 스크립트
├── artifacts/              # 📂 시나리오 명세 및 수집된 데이터 산출물
│   ├── scenarios/          #   └── 9개의 난이도별 시나리오 명세서 (.md)
│   └── results/            #   └── 시나리오별 평가 리포트 및 크롤링 결과 JSON
├── docs/                   # 📖 Lessons Summary 및 강의 교재 지원 문서
├── reference/              # 📚 LangChain/LangGraph 규칙 매뉴얼 및 핵심 가이드
├── samples/                # 🍌 AI 이미지 생성(Nano Banana) 테스트 코드
├── install/                # 환경 설치 스크립트 모음
├── start_vnc.sh            # VNC + noVNC 구동 스크립트
└── README.md               # 프로젝트 메인 명세서
```

---

## ▶️ 실시간 서빙 및 채팅 UI 가동 가이드

노트북 실습이 완료되면, 에이전트 팀을 실제 서비스 웹 UI 형태로 구동할 수 있습니다. 

### 1. 백엔드 서버(FastAPI) 가동
에이전트들을 API로 서빙하는 엔드포인트를 노출시킵니다.
```bash
python app/server.py --port 8000
```
* 서버 실행 후 `http://localhost:8000/docs` 에서 에이전트 API(Invoke / Stream) 작동 상태를 테스트해 볼 수 있습니다.

### 2. 터미널 테스트 CLI 가동
```bash
python app/client.py
# /switch navigator_agent 명령어 등을 입력하여 동작 에이전트를 스위칭할 수 있습니다.
```

### 3. Streamlit 웹 채팅 UI 가동
```bash
streamlit run app/ui.py
```
* 브라우저에서 `http://localhost:8501`에 접속한 뒤 사이드바에서 **`supervisor_agent`** 또는 **`navigator_agent`**를 선택하고 자연어로 대화를 나누어 보세요. VNC 화면을 함께 띄워놓으면 에이전트가 내 말에 따라 사이트를 자율 탐색하는 과정을 입체적으로 관찰할 수 있습니다.

---

## 🛠️ 에이전트 고도화 가이드

성공적인 미션 클리어를 위해 교육생들은 다음의 핵심 영역을 집중적으로 개선해야 합니다.

1. **시스템 프롬프트 튜닝 (`app/prompts/`)**:
   * Navigator가 타겟 사이트의 로딩 속도를 분석하고 대기 시간을 동적으로 인지하게 하거나, Coder가 더욱 안정적인 에러 핸들링 코드를 작성하도록 페르소나와 제약조건을 고도화합니다.
2. **에이전트 조립 구조 개선 (`app/agents/`)**:
   * LLM 파라미터(온도 조절 등)를 미세조정하거나, 에이전트 간 주고받는 맥락(Context Schema) 정보에 튜닝된 데이터를 추가해 협업 품질을 향상시킵니다.
3. **전문 도구 확장 (`app/tools/`)**:
   * DOM 트리를 축약하여 토큰 소모를 방지하는 `extract_dom_skeleton` 같은 신규 고성능 도구를 직접 개발하고 장착해 에이전트의 물리적 능력을 강화합니다.

자세한 미션 빌드업 절차는 **[Mission.md]** 파일을 열어 Step-by-step 지침에 따라 차근차근 도전을 완료하세요!

---
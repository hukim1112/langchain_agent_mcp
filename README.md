# 🔌 LangChain Agent × MCP 실습 프로젝트

> LangChain 에이전트를 구축하고, FastMCP 서버를 직접 만들어 연동하는 실습 프로젝트입니다.

---

## 🔍 프로젝트 소개

이 프로젝트에서는 **4가지 핵심 과제**를 수행합니다.

1. **기존 에이전트 실행 및 커스텀 에이전트 추가** — 시스템 전반 및 레지스트리 작동법 학습
2. **MCP 서버 구축** — 기존 LangChain Retrieval 도구를 FastMCP 서버로 래핑
3. **Agent ↔ MCP 연동** — 에이전트가 MCP 서버를 동적으로 탐색·호출하도록 구현
4. **에이전트 고도화** — Supervisor 하위 에이전트 연결, Middleware 적용 등

자세한 미션 수행 절차는 **[Mission.md](Mission.md)** 를 참고하세요.

---

## 🚀 시작하기 (환경 세팅)

Codespaces 또는 로컬 WSL2(우분투) 환경에서 아래 명령어를 실행하세요.

```bash
bash install.sh
```

설치 스크립트가 하는 일:
1. 시스템 패키지 설치 (`poppler-utils`)
2. Python 라이브러리 설치 (`requirements.txt` + `gdown`)
3. MCP 서버용 데이터 다운로드 (한국은행 보고서, Chinook DB, 논문 벡터스토어)

### 환경 변수 설정

`.env_template`을 복사하여 `.env` 파일을 만들고 API 키를 입력하세요.

```bash
cp .env_template .env
```

```env
OPENAI_API_KEY="your-api-key"
GOOGLE_API_KEY="your-api-key"
TAVILY_API_KEY="your-tavily-api-key"
```

### LangSmith 트레이싱 (권장)

에이전트의 내부 동작을 추적하고 디버깅하려면 [LangSmith](https://smith.langchain.com) 키도 설정하세요.

```env
LANGCHAIN_API_KEY="your-langsmith-key"
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=langchain_agent_mcp
```

---

## 📂 프로젝트 구조

```
langchain_agent_mcp/
│
├── app/                        # 🧠 에이전트 시스템
│   ├── agents/                 #   에이전트 정의
│   │   ├── __init__.py         #     에이전트 레지스트리 (서버 자동 등록)
│   │   ├── supervisor.py       #     Supervisor 에이전트 (총괄)
│   │   ├── coder.py            #     Coder 에이전트 (코드 작성/실행)
│   │   ├── chatbot.py          #     범용 챗봇
│   │   └── mcp_agent.py        #     ⭐ MCP 연동 에이전트 (미션에서 구현)
│   ├── tools/                  #   에이전트 도구
│   │   ├── __init__.py         #     도구 그룹 등록
│   │   ├── coder.py            #     파일 읽기/쓰기/실행 도구
│   │   ├── supervisor_tools.py #     웹 검색, 이미지 분석 도구
│   │   ├── mcp_tools.py        #     ⭐ MCP 동적 연동 도구 (미션에서 구현)
│   │   └── common.py           #     공통 유틸리티
│   ├── prompts/                #   시스템 프롬프트
│   ├── server.py               #   FastAPI 백엔드 서버
│   ├── client.py               #   터미널 테스트 CLI
│   ├── ui.py                   #   Streamlit 채팅 UI
│   └── schemas.py              #   데이터 스키마
│
├── mcp/                        # 🔌 MCP 서버 영역
│   ├── rag_database/           #   Retriever 래퍼 모듈 (다운로드됨)
│   │   ├── bok_report.py       #     한국은행 보고서 Self-Querying
│   │   ├── chinook_sql.py      #     Chinook DB Text2SQL (LangGraph)
│   │   └── paper_rag.py        #     논문 벡터 검색 (MMR)
│   ├── bok_server.py           #   ⭐ BOK MCP 서버 (미션에서 구현)
│   ├── chinook_server.py       #   ⭐ Chinook MCP 서버 (미션에서 구현)
│   ├── papers_server.py        #   ⭐ Papers MCP 서버 (미션에서 구현)
│   ├── MCP.md                  #   에이전트용 서버 컨텍스트 파일
│   ├── run_mcp_servers.sh      #   서버 일괄 실행 스크립트
│   ├── test_retrievers.py      #   Retriever 동작 검증 스크립트
│   └── test_mcp_client.py      #   MCP 클라이언트 테스트
│
├── install.sh                  # 환경 설치 + 데이터 다운로드
├── requirements.txt            # Python 패키지 목록
├── Mission.md                  # ⭐ 미션 수행 가이드 (Step-by-step)
└── README.md                   # 프로젝트 명세서 (이 파일)
```

> ⭐ 표시된 파일은 **교육생이 직접 구현해야 하는 파일**입니다.

---

## ▶️ 서버 실행 가이드

### 1. MCP 서버 실행 (포트 8010~8012)

```bash
bash mcp/run_mcp_servers.sh
```

### 2. 에이전트 API 서버 실행 (포트 8000)

```bash
python app/server.py --port 8000
```

### 3. Streamlit 채팅 UI 실행

```bash
streamlit run app/ui.py
```

브라우저에서 `http://localhost:8501` 접속 후, 사이드바에서 `mcp_agent`를 선택하여 대화해보세요.

---

## 📋 미션 수행

**[Mission.md](Mission.md)** 파일에 Step-by-step 미션 가이드가 정리되어 있습니다.

`main` 브랜치의 현재 상태에서 출발하여, 4단계 미션을 순서대로 완료하세요.
예제 코드는 instructor 브랜치에서 확인할 수 있습니다.

# 🎯 Mission Guide

이 문서는 `main` 브랜치를 기준으로, 교육생이 직접 수행해야 하는 미션을 안내합니다.

---

## 사전 준비

미션을 시작하기 전에 아래 항목을 먼저 완료하세요.

```bash
# 1. 의존성 설치 + 데이터 다운로드
bash install.sh

# 2. .env 파일 생성 및 API 키 입력
cp .env_template .env
# OPENAI_API_KEY, GOOGLE_API_KEY, TAVILY_API_KEY 등 기입
```

---

## Mission 1: 기존 에이전트 실행 및 커스텀 에이전트 추가

본격적인 MCP 연동에 앞서, 프로젝트의 기존 에이전트 시스템 구조를 이해하고 UI 상에서 테스트해보는 단계입니다.

### 1-1. 서버 실행 및 UI 체험

FastAPI 에이전트 백엔드 서버와 Streamlit 채팅 UI를 실행하여 기본 제공되는 `Chatbot` 및 `Coder` 에이전트가 정상 작동하는지 확인해 봅니다.

```bash
# 1. 에이전트 백엔드 서버 실행 (포트 8000)
python app/server.py

# 2. Streamlit UI 실행 (포트 8501)
streamlit run app/ui.py
```

- 웹 브라우저로 `http://localhost:8501`에 접속합니다.
- 왼쪽 사이드바에서 `chatbot` 혹은 `coder` 에이전트를 선택하고 대화를 시도해 봅니다.
  - `chatbot`: 도구(Tool) 없이 단순 챗백(자연어 대화)을 처리하는 에이전트
  - `coder`: 파일 작업이나 스크립트 실행이 가능한 코드 생성 및 자가수정 에이전트

### 1-2. 커스텀 에이전트 추가 및 도구 연결

에이전트 레지스트리(Agent Registry)의 등록 방식을 학습하기 위해, 아주 간단한 도구를 가진 신규 에이전트를 직접 추가하고 UI에 노출시켜 봅니다.

#### 1) Mock 도구 또는 기본 도구 생성
`app/tools/simple_agent.py`에 에이전트가 호출할 간단한 도구를 정의합니다.
예를 들어, 사용자 이름을 조회하는 Mock 도구를 만듭니다.

```python
from langchain_core.tools import tool

@tool(parse_docstring=True)
def get_user_name() -> str:
    """현재 시스템의 로그인 사용자 이름을 조회합니다."""
    return "홍길동"
```

#### 2) 커스텀 에이전트 모듈 생성 (`app/agents/simple_agent.py`)
`app/agents/chatbot.py`나 `app/agents/coder.py` 구조를 참고하여 간단한 챗봇 에이전트를 설계합니다. 시스템 프롬프트에 위에서 생성한 도구를 반드시 사용하라는 내용을 기술합니다.

```python
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from app.tools import get_user_name

def create_simple_agent():
    model = init_chat_model("google_genai:gemini-2.5-flash", temperature=0.1)
    checkpointer = InMemorySaver()
    
    return create_agent(
        model=model,
        system_prompt="당신은 사용자의 정보를 친근하게 안내하는 에이전트입니다. get_user_name 도구를 사용해 사용자의 이름을 알아내고 친절하게 부르며 대화하세요.",
        tools=[get_user_name],
        checkpointer=checkpointer,
        name="simple_agent"
    )

agent_executor = create_simple_agent()
```

#### 3) 에이전트 레지스트리에 등록 (`app/agents/__init__.py`)
`app/agents/__init__.py` 파일의 `AGENT_REGISTRY` 리스트에 위에서 만든 에이전트 정보를 추가합니다.

```python
    {
        "name": "simple_agent",
        "module": "app.agents.simple_agent",
        "prefix": "/simple_agent",
        "tags": ["Simple Agent"],
        "description": "사용자 이름을 조회하는 간단한 테스트용 에이전트"
    }
```

#### 4) 동작 확인
FastAPI 백엔드 서버를 재시작(`python app/server.py`)하면 새로운 에이전트 엔드포인트 `/simple_agent`가 자동으로 등록됩니다. 
Streamlit UI(`http://localhost:8501`)를 새로고침한 뒤 `simple_agent`를 선택해 "안녕? 내 이름이 뭔지 알아?"라고 대화하여 정상적으로 Mock 도구가 실행되고 이름이 노출되는지 검증합니다.

---

## Mission 2: MCP 서버 만들기

`mcp/rag_database/` 폴더에 이미 구현되어 있는 retriever 래퍼 3종이 있습니다.

| 모듈 | 데이터 | 검색 방식 |
|------|--------|-----------|
| `bok_report.py` | 한국은행 분기 보고서 | Self-Querying (메타데이터 필터링) |
| `chinook_sql.py` | Chinook 음악 DB | Text2SQL (LangGraph 워크플로우) |
| `paper_rag.py` | Modular RAG 논문 | 벡터 유사도 검색 (MMR) |

서버를 개발하기 전, 먼저 각 데이터와 검색 모듈이 올바르게 로드되는지 확인하기 위해 아래 검증 스크립트를 실행합니다.

```bash
python mcp/test_retrievers.py
```

3개의 리트리버가 에러 없이 정상적으로 결과를 반환하면 준비 완료입니다. 이 래퍼들을 **FastMCP 서버**로 감싸는 것이 두 번째 미션입니다.

### 할 일

1. `mcp/bok_server.py` 생성 — BOK 보고서 검색 서버 (포트 8010)
2. `mcp/chinook_server.py` 생성 — Chinook Text2SQL 서버 (포트 8011)
3. `mcp/papers_server.py` 생성 — 논문 RAG 검색 서버 (포트 8012)

### 구현 힌트

각 서버의 기본 골격은 아래와 같습니다. retriever를 초기화하고, `@mcp.tool()`로 감싸면 됩니다.

```python
from fastmcp import FastMCP
from rag_database import bok_report  # 래퍼 임포트

# Retriever 초기화
retriever = bok_report.get_retriever(...)

# FastMCP 서버 정의
mcp = FastMCP("BOK Report Search")

@mcp.tool()
def query_bok_reports(query: str) -> str:
    """한국은행 보고서를 검색합니다."""
    results = retriever.invoke(query)
    # 결과를 문자열로 정리해서 반환
    ...

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8010)
```

### 검증

서버를 띄우고, `mcp/test_mcp_client.py`를 참고하여 `fastmcp.Client`로 연결해보세요.

```python
from fastmcp import Client

async with Client("http://localhost:8010/sse") as c:
    tools = await c.list_tools()    # 도구 목록 확인
    result = await c.call_tool("query_bok_reports", {"query": "2024년 3분기 반도체"})
    print(result.content)
```

도구 목록이 조회되고, 검색 결과가 반환되면 Mission 2 클리어입니다.

---

## Mission 3: Agent ↔ MCP 연동

MCP 서버가 준비되었으니, 에이전트가 이 서버들을 **동적으로** 탐색하고 호출할 수 있게 만들어야 합니다.

### 3-1. MCP 컨텍스트 파일 작성

`mcp/MCP.md` 파일을 만들어서, 에이전트가 참고할 수 있는 서버 목록을 정리하세요.

```markdown
# Available MCP Servers

| 서버명 | URL | 설명 |
|--------|-----|------|
| BOK Report Search | http://localhost:8010/sse | 한국은행 보고서 검색 |
| Chinook Music DB | http://localhost:8011/sse | 음악 DB 자연어 질의 |
| Papers RAG Search | http://localhost:8012/sse | 논문 검색 |
```

### 3-2. MCP 도구 구현

`app/tools/mcp_tools.py`에 아래 3개의 도구를 구현하세요.

| 도구 | 역할 |
|------|------|
| `read_mcp_context` | `MCP.md`를 읽어서 사용 가능한 서버 목록 반환 |
| `list_mcp_tools` | 특정 서버 URL에 연결하여 제공 도구 목록 조회 |
| `execute_mcp_tool` | 특정 서버의 도구를 실행하고 결과 반환 |

에이전트는 이 3개의 도구만으로 어떤 MCP 서버든 탐색하고 호출할 수 있어야 합니다.

#### 주의 사항

- `list_mcp_tools`와 `execute_mcp_tool`은 **`async def`**로 작성하세요. FastAPI 서버 내부에서 호출되기 때문에 기존 이벤트 루프와 충돌하지 않으려면 비동기 함수여야 합니다.
- `execute_mcp_tool`의 `arguments` 파라미터는 `dict` 타입으로 받으세요. JSON 문자열이 아닙니다.
- `fastmcp.Client`의 `call_tool()` 결과는 `CallToolResult` 객체이며, `.content`로 접근합니다.

### 3-3. MCP 에이전트 생성

`app/agents/mcp_agent.py`에 MCP 전용 에이전트를 만드세요.

- `app/prompts/mcp_agent.py`에 시스템 프롬프트를 작성하고
- `app/tools/__init__.py`에 `tools_mcp` 그룹을 등록하고
- `app/agents/__init__.py`의 `AGENT_REGISTRY`에 에이전트를 추가하세요

프롬프트에는 **3단계 프로토콜**을 명시하는 게 핵심입니다:

```
1단계: read_mcp_context → 서버 목록/URL 파악
2단계: list_mcp_tools → 해당 서버의 도구와 파라미터 확인
3단계: execute_mcp_tool → 도구 실행
```

### 검증

```bash
# MCP 서버 3종 실행
bash mcp/run_mcp_servers.sh

# 에이전트 서버 실행
python app/server.py

# Streamlit UI에서 mcp_agent를 선택하고 아래 질문을 해보세요
```

- "어떤 MCP에 접근할 수 있어?"
- "음악 DB에서 가장 인기있는 아티스트 알려줘"
- "2024년 3분기 반도체 동향 요약해줘"
- "Modular RAG의 핵심 아이디어가 뭐야?"

3개 서버 모두 정상 응답하면 Mission 3 클리어입니다.

---

## Mission 4: 에이전트 고도화

기본 연동이 완료되었으면, 에이전트들의 구조를 고도화하고 기능을 개선해 봅시다.

### 4-1. Supervisor에 MCP 에이전트 연결 (Multi-Agent 구성)

현재 `Supervisor` 에이전트(`app/agents/supervisor.py`)는 `Coder` 에이전트만 하위 에이전트(`chat_to_coder`)로 두고 있으며, MCP 도구들(`read_mcp_context`, `list_mcp_tools`, `execute_mcp_tool`)은 자신이 직접 소유하여 실행하고 있습니다.

이 구조를 개선하여, 외부 데이터 검색이나 보고서/논문 조회 요청이 들어왔을 때 **Supervisor가 직접 MCP 도구를 실행하는 것이 아니라, MCP 에이전트(`mcp_agent`)에게 작업을 위임(Handoff)**하도록 구현해 봅시다.

#### 수행 단계
1. **MCP 에이전트 임포트 및 생성**:
   `app/agents/supervisor.py`에서 `app.agents.mcp_agent`로부터 `create_mcp_agent`를 가져와 전역 변수로 `GLOBAL_MCP_AGENT`를 생성합니다.
2. **Handoff 도구 (`chat_to_mcp`) 정의**:
   `chat_to_coder` 구현을 참고하여, `GLOBAL_MCP_AGENT`를 비동기적으로 실행하고 답변을 받아오는 `@tool` 함수 `chat_to_mcp`를 작성합니다.
3. **Supervisor 도구 및 프롬프트 수정**:
   - `tools_supervisor` 목록에서 직접적인 MCP 도구들(`read_mcp_context`, `list_mcp_tools`, `execute_mcp_tool`)을 제거하고, 대신 `chat_to_mcp` 도구를 추가합니다. (`app/tools/__init__.py` 수정 혹은 `supervisor.py`에서 도구 리스트 조정)
   - `app/prompts/supervisor.py`에서 Supervisor가 직접 MCP 3단계 프로토콜을 수행하도록 안내하던 내용을 지우고, 대신 "외부 보고서, 음악 DB, 학술 논문 검색 등이 필요한 질문은 `chat_to_mcp` 도구를 사용하여 MCP 에이전트에게 전달하라"고 역할을 재정의합니다.

#### 구현 힌트
`app/agents/supervisor.py`에 추가할 도구 예시:
```python
@tool(parse_docstring=True)
async def chat_to_mcp(task_description: str, runtime: ToolRuntime, config: RunnableConfig) -> str:
    """한국은행 보고서 검색, Chinook 음악 DB 질의, RAG 논문 검색 등 외부 MCP 서버의 데이터 조회가 필요할 때 사용합니다.
    
    Args:
        task_description: MCP 에이전트에게 조회를 요청할 질문이나 구체적인 작업 요구사항
    """
    print(f"\n👨‍💼 [Supervisor] MCP 에이전트와 대화 중...")
    
    inner_config = config.copy() if config else {}
    inner_config["configurable"] = inner_config.get("configurable", {}).copy()
    inner_config["configurable"]["thread_id"] = config.get("configurable", {}).get("thread_id", "default_thread")
    
    result = await GLOBAL_MCP_AGENT.ainvoke(
        {"messages": [("user", task_description)]},
        config=inner_config
    )
    return result["messages"][-1].content
```

### 4-2. Middleware 적용

`langchain.agents.middleware`를 활용하면 에이전트에 파일 시스템 검색, 로깅 등 부가 기능을 끼울 수 있습니다.
`coder.py`를 참고하여 MCP 에이전트에도 적절한 Middleware를 적용해보세요.

### 4-3. 프롬프트 튜닝

실제로 대화해보면 개선할 점이 보일 겁니다.

- 검색 결과가 없을 때 쿼리를 자동으로 변형해서 재시도하게 만들기
- 여러 서버의 결과를 종합하여 답변하게 만들기
- 출처(어떤 서버의 어떤 도구를 썼는지)를 항상 명시하게 만들기

---
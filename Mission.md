# 🎯 Mission Guide

이 문서는 `main` 브랜치를 기준으로, 교육생이 직접 수행해야 하는 미션을 안내합니다.

> 정답 코드는 `instructor` 브랜치에 있습니다. 막힐 때 참고하세요.
> 단, 먼저 직접 해보는 것을 강력히 권장합니다.

---

## 사전 준비

미션을 시작하기 전에 아래 항목을 먼저 완료하세요.

```bash
# 1. 의존성 설치 + 데이터 다운로드
bash install.sh

# 2. .env 파일 생성 및 API 키 입력
cp .env_template .env
# OPENAI_API_KEY, TAVILY_API_KEY 등 기입

# 3. Retriever 래퍼가 정상 동작하는지 확인
python mcp/test_retrievers.py
```

3개의 retriever가 모두 결과를 반환하면 준비 완료입니다.

---

## Mission 1: MCP 서버 만들기

`mcp/rag_database/` 폴더에 이미 다운로드된 retriever 래퍼 3종이 있습니다.

| 모듈 | 데이터 | 검색 방식 |
|------|--------|-----------|
| `bok_report.py` | 한국은행 분기 보고서 | Self-Querying (메타데이터 필터링) |
| `chinook_sql.py` | Chinook 음악 DB | Text2SQL (LangGraph 워크플로우) |
| `paper_rag.py` | Modular RAG 논문 | 벡터 유사도 검색 (MMR) |

이 래퍼들을 **FastMCP 서버**로 감싸는 것이 첫 번째 미션입니다.

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

도구 목록이 조회되고, 검색 결과가 반환되면 Mission 1 클리어입니다.

---

## Mission 2: Agent ↔ MCP 연동

MCP 서버가 준비되었으니, 에이전트가 이 서버들을 **동적으로** 탐색하고 호출할 수 있게 만들어야 합니다.

### 2-1. MCP 컨텍스트 파일 작성

`mcp/MCP.md` 파일을 만들어서, 에이전트가 참고할 수 있는 서버 목록을 정리하세요.

```markdown
# Available MCP Servers

| 서버명 | URL | 설명 |
|--------|-----|------|
| BOK Report Search | http://localhost:8010/sse | 한국은행 보고서 검색 |
| Chinook Music DB | http://localhost:8011/sse | 음악 DB 자연어 질의 |
| Papers RAG Search | http://localhost:8012/sse | 논문 검색 |
```

### 2-2. MCP 도구 구현

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

### 2-3. MCP 에이전트 생성

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

3개 서버 모두 정상 응답하면 Mission 2 클리어입니다.

---

## Mission 3: 에이전트 고도화

기본 연동이 완료되었으면, 에이전트를 더 똑똑하게 만들어봅시다.

### 3-1. 장기 메모리 적용

현재 `InMemorySaver`는 서버를 재시작하면 대화 기록이 사라집니다.
SQLite 기반 체크포인터로 교체하여 대화 기록이 영구 보존되도록 하세요.

```python
from langgraph.checkpoint.sqlite import SqliteSaver
checkpointer = SqliteSaver.from_conn_string("checkpoints.db")
```

### 3-2. Middleware 적용

`langchain.agents.middleware`를 활용하면 에이전트에 파일 시스템 검색, 로깅 등 부가 기능을 끼울 수 있습니다.
`coder.py`를 참고하여 MCP 에이전트에도 적절한 Middleware를 적용해보세요.

### 3-3. 프롬프트 튜닝

실제로 대화해보면 개선할 점이 보일 겁니다.

- 검색 결과가 없을 때 쿼리를 자동으로 변형해서 재시도하게 만들기
- 여러 서버의 결과를 종합하여 답변하게 만들기
- 출처(어떤 서버의 어떤 도구를 썼는지)를 항상 명시하게 만들기

---

## 참고: 브랜치 구조

| 브랜치 | 용도 |
|--------|------|
| `main` | 교육생 시작점 (미션 미완성 상태) |
| `instructor` | 강사용 정답 코드 (3개 미션 완료 상태) |

막히면 instructor 브랜치의 diff를 확인하세요:

```bash
git diff main..instructor -- mcp/
git diff main..instructor -- app/tools/mcp_tools.py
git diff main..instructor -- app/agents/mcp_agent.py
```

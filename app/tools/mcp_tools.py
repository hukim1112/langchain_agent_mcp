# =====================================================================
# MCP 연동 도구 (Supervisor Agent용)
#
# 에이전트가 MCP 서버를 동적으로 탐색하고 호출할 수 있게 하는 도구 3종:
#   1. read_mcp_context  — MCP.md를 읽어 사용 가능한 서버 목록 파악
#   2. list_mcp_tools    — 특정 MCP 서버의 제공 도구 목록 조회
#   3. execute_mcp_tool  — 특정 MCP 서버의 도구 실행
# =====================================================================

import os
import json
import asyncio
from langchain_core.tools import tool


# ── MCP.md 경로 ──
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MCP_CONTEXT_PATH = os.path.join(_PROJECT_ROOT, "mcp", "MCP.md")


@tool(parse_docstring=True)
def read_mcp_context() -> str:
    """사용 가능한 MCP 서버 목록과 사용법을 조회합니다.
    MCP 서버에 연결하기 전에 반드시 이 도구를 먼저 호출하세요.
    """
    if not os.path.exists(MCP_CONTEXT_PATH):
        return "⚠️ MCP.md 파일을 찾을 수 없습니다. MCP 서버가 설정되지 않았을 수 있습니다."

    with open(MCP_CONTEXT_PATH, "r", encoding="utf-8") as f:
        return f.read()


@tool(parse_docstring=True)
def list_mcp_tools(server_url: str) -> str:
    """특정 MCP 서버에 연결하여 제공하는 도구 목록을 조회합니다.

    Args:
        server_url: MCP 서버 SSE URL (예: 'http://localhost:8010/sse')
    """
    from fastmcp import Client

    async def _list():
        async with Client(server_url) as client:
            tools = await client.list_tools()
            result = []
            for t in tools:
                result.append(
                    f"• {t.name}: {t.description or '설명 없음'}\n"
                    f"  파라미터: {json.dumps({p.name: p.description or p.type for p in t.parameters}, ensure_ascii=False)}"
                )
            return f"🔧 {server_url} 의 도구 목록 ({len(tools)}개):\n\n" + "\n\n".join(result)

    return asyncio.run(_list())


@tool(parse_docstring=True)
def execute_mcp_tool(server_url: str, tool_name: str, arguments: str = "{}") -> str:
    """특정 MCP 서버의 도구를 실행하고 결과를 반환합니다.

    Args:
        server_url: MCP 서버 SSE URL (예: 'http://localhost:8010/sse')
        tool_name: 실행할 도구 이름 (예: 'query_bok_reports')
        arguments: 도구에 전달할 인자 (JSON 문자열, 예: '{"query": "반도체 동향"}')
    """
    from fastmcp import Client

    async def _execute():
        async with Client(server_url) as client:
            args = json.loads(arguments)
            result = await client.call_tool(tool_name, args)
            # CallToolResult.content에 TextContent 리스트가 들어있음
            if hasattr(result, 'content'):
                return "\n".join(
                    item.text if hasattr(item, 'text') else str(item)
                    for item in result.content
                )
            return str(result)

    return asyncio.run(_execute())

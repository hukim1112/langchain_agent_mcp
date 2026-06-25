# =====================================================================
# MCP 연동 도구
#
# 에이전트가 MCP 서버를 동적으로 탐색하고 호출할 수 있게 하는 도구 3종:
#   1. read_mcp_context  — MCP.md를 읽어 사용 가능한 서버 목록 파악
#   2. list_mcp_tools    — 특정 MCP 서버의 제공 도구 목록 조회
#   3. execute_mcp_tool  — 특정 MCP 서버의 도구 실행
# =====================================================================

import os
from langchain_core.tools import tool
from fastmcp import Client


# ── MCP.md 경로 ──
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MCP_CONTEXT_PATH = os.path.join(_PROJECT_ROOT, "mcp", "MCP.md")


@tool
def read_mcp_context() -> str:
    """MCP 서버들에 대한 역할과 설명(맥락)이 정리된 MCP.md 파일의 내용을 실시간으로 읽어옵니다.
    특정 비즈니스 질문에 어떤 MCP 서버의 도구를 사용해야 할지 판단하는 기준으로 활용하세요.
    """
    if os.path.exists(MCP_CONTEXT_PATH):
        with open(MCP_CONTEXT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return "⚠️ MCP.md 파일을 찾을 수 없습니다. MCP 서버가 설정되지 않았을 수 있습니다."


@tool
async def list_mcp_tools(url: str) -> str:
    """지정된 MCP 서버 URL(url)이 실시간으로 제공하는 모든 도구 목록과 파라미터 스키마를 가져옵니다.

    Args:
        url: 조회하고자 하는 MCP 서버의 전체 HTTP/SSE 엔드포인트 주소 (예: 'http://localhost:8010/sse')
    """
    try:
        client = Client(url)
        async with client:
            tools_response = await client.list_tools()

            tools_list = []
            for t in tools_response:
                tools_list.append({
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.inputSchema
                })
            return str(tools_list)
    except Exception as e:
        return f"MCP 서버 주소 '{url}'로부터 도구 목록을 가져오는 데 실패했습니다: {str(e)}"


@tool
async def execute_mcp_tool(url: str, tool_name: str, arguments: dict) -> str:
    """지정된 MCP 서버 URL(url)의 특정 도구(tool_name)를 입력한 인자(arguments)로 실행하고 결과를 반환합니다.

    Args:
        url: 실행할 도구가 위치한 MCP 서버의 전체 HTTP/SSE 엔드포인트 주소 (예: 'http://localhost:8010/sse')
        tool_name: 실행하고자 하는 도구 이름
        arguments: 도구 실행에 필요한 파라미터 딕셔너리
    """
    try:
        client = Client(url)
        async with client:
            result = await client.call_tool(tool_name, arguments)
            return str(result.content)
    except Exception as e:
        return f"MCP 서버 주소 '{url}'의 도구 '{tool_name}' 실행 중 에러 발생: {str(e)}"

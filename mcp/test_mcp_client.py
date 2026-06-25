"""MCP 서버 연결 테스트 — fastmcp.Client로 도구 조회 및 호출"""
import asyncio
from fastmcp import Client

async def test():
    url = "http://localhost:8010/sse"
    print(f"🔗 연결 중: {url}")
    
    async with Client(url) as c:
        # 1. 도구 목록 조회
        tools = await c.list_tools()
        print(f"\n=== 도구 목록 ({len(tools)}개) ===")
        for t in tools:
            print(f"  • {t.name}: {t.description}")
        
        # 2. 검색 실행
        print("\n=== 검색 테스트: '2024년 1분기 자동차 동향' ===")
        result = await c.call_tool("query_bok_reports", {"query": "2024년 1분기 자동차 동향"})
        # CallToolResult는 .content 속성에 TextContent 리스트를 가짐
        if hasattr(result, 'content'):
            for item in result.content:
                print(str(item.text)[:500] if hasattr(item, 'text') else str(item)[:500])
        else:
            print(str(result)[:500])

    print("\n✅ MCP 클라이언트 테스트 완료!")

asyncio.run(test())


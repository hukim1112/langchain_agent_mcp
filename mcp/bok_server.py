# =====================================================================
# 한국은행 분기 보고서 검색 MCP 서버
#
# Self-Querying 방식으로 메타데이터(연도, 분기)를 자동 필터링하여
# 한국은행 주력산업 모니터링 보고서를 검색합니다.
#
# 실행: python mcp/bok_server.py
# 포트: 8010 (SSE)
# =====================================================================

try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import os
import sys
from dotenv import load_dotenv

# 프로젝트 루트의 .env 로드
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)

from fastmcp import FastMCP
from langchain_openai import OpenAIEmbeddings

# ── Retriever 초기화 (서버 기동 시 1회) ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from rag_database import bok_report

DB_DIR = os.path.join(SCRIPT_DIR, "report_db")
embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")
retriever = bok_report.get_retriever(
    embedding_model=embedding_model,
    db_directory=DB_DIR
)
print(f"✅ BOK Report Retriever 로드 완료 (DB: {DB_DIR})")


# ── FastMCP 서버 정의 ──
mcp = FastMCP(
    "BOK Report Search",
    instructions="한국은행 주력산업 모니터링 보고서를 검색합니다. 연도, 분기, 업종 등의 조건으로 검색할 수 있습니다."
)


@mcp.tool()
def query_bok_reports(query: str) -> str:
    """한국은행 주력산업 모니터링 보고서를 검색합니다.
    Self-Querying 방식으로 연도/분기 메타데이터를 자동 필터링합니다.

    Args:
        query: 검색 질의 (예: '2024년 3분기 반도체 동향')
    """
    results = retriever.invoke(query)

    if not results:
        return "검색 결과가 없습니다."

    output_parts = [f"📊 검색 결과: {len(results)}건\n"]
    for i, doc in enumerate(results):
        meta = doc.metadata
        year = meta.get("year", "?")
        quarter = meta.get("quarter", "?")
        output_parts.append(
            f"[{i+1}] {year}년 {quarter}분기 | 페이지 {meta.get('page_label', '?')}\n"
            f"{doc.page_content[:500]}\n"
        )

    return "\n".join(output_parts)


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8010)

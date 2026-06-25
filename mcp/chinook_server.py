# =====================================================================
# Chinook 음악 데이터베이스 Text2SQL MCP 서버
#
# 자연어 질문을 SQL로 변환하여 Chinook SQLite DB를 질의합니다.
# LangGraph 워크플로우(write_query → execute_query → generate_answer)로 구성.
#
# 실행: python mcp/chinook_server.py
# 포트: 8011 (SSE)
# =====================================================================

import os
import sys
from dotenv import load_dotenv

# 프로젝트 루트의 .env 로드
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)

from fastmcp import FastMCP

# ── Retriever 초기화 (서버 기동 시 1회) ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from rag_database import chinook_sql

DB_PATH = os.path.join(SCRIPT_DIR, "sqlite", "Chinook.db")
sql_graph = chinook_sql.get_retriever(
    model_name="gpt-4o",
    db_directory=DB_PATH
)
print(f"✅ Chinook SQL Graph 로드 완료 (DB: {DB_PATH})")


# ── FastMCP 서버 정의 ──
mcp = FastMCP(
    "Chinook Music DB",
    instructions="Chinook 음악 데이터베이스에 자연어로 질의합니다. 아티스트, 앨범, 고객, 매출 등을 조회할 수 있습니다."
)


@mcp.tool()
def query_chinook_database(question: str) -> str:
    """Chinook 음악 데이터베이스에 자연어로 질의합니다.
    내부적으로 SQL을 자동 생성하여 실행하고 결과를 답변으로 생성합니다.

    Args:
        question: 자연어 질문 (예: '가장 많은 앨범을 산 고객은?')
    """
    result = sql_graph.invoke({"question": question})
    
    return (
        f"📊 생성된 SQL:\n{result.get('query', 'N/A')}\n\n"
        f"💾 실행 결과:\n{result.get('result', 'N/A')}\n\n"
        f"💬 답변:\n{result.get('answer', 'N/A')}"
    )


@mcp.tool()
def get_chinook_schema() -> str:
    """Chinook 데이터베이스의 테이블 스키마 정보를 반환합니다.
    어떤 테이블과 컬럼이 있는지 확인할 때 사용합니다.
    """
    from langchain_community.utilities import SQLDatabase
    db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
    return db.get_table_info()


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8011)

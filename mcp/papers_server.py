# =====================================================================
# Modular RAG 논문 검색 MCP 서버
#
# ChromaDB 벡터스토어에서 MMR 방식으로 논문 내용을 검색합니다.
# 논문에 포함된 이미지 목록도 조회할 수 있습니다.
#
# 실행: python mcp/papers_server.py
# 포트: 8012 (SSE)
# =====================================================================

try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import os
import sys
import glob
from dotenv import load_dotenv

# 프로젝트 루트의 .env 로드
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)

from fastmcp import FastMCP

# ── Retriever 초기화 (서버 기동 시 1회) ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from rag_database import paper_rag

DB_DIR = os.path.join(SCRIPT_DIR, "papers_rag")
retriever = paper_rag.get_retriever(db_directory=DB_DIR)
print(f"✅ Paper RAG Retriever 로드 완료 (DB: {DB_DIR})")


# ── FastMCP 서버 정의 ──
mcp = FastMCP(
    "Papers RAG Search",
    instructions="Modular RAG 논문의 내용을 검색합니다. 논문의 개념, 아키텍처, 모듈 등을 질의할 수 있습니다."
)


@mcp.tool()
def query_papers(query: str, top_k: int = 5) -> str:
    """Modular RAG 논문에서 관련 내용을 검색합니다.
    MMR(Maximal Marginal Relevance) 방식으로 다양한 결과를 반환합니다.

    Args:
        query: 검색 질의 (예: 'Modular RAG의 정의')
        top_k: 반환할 결과 수 (기본값: 5)
    """
    results = retriever.invoke(query)

    if not results:
        return "검색 결과가 없습니다."

    output_parts = [f"📄 검색 결과: {len(results)}건\n"]
    for i, doc in enumerate(results):
        source = doc.metadata.get("source", "unknown")
        has_image = "🖼️" if "extracted_images" in doc.page_content else ""
        output_parts.append(
            f"[{i+1}] {has_image} Source: {os.path.basename(source)}\n"
            f"{doc.page_content[:500]}\n"
        )

    return "\n".join(output_parts)


@mcp.tool()
def list_paper_images() -> str:
    """논문에서 추출된 이미지 파일 목록을 반환합니다."""
    image_dir = os.path.join(DB_DIR, "extracted_images")
    if not os.path.exists(image_dir):
        return "이미지 폴더가 존재하지 않습니다."

    images = sorted(glob.glob(os.path.join(image_dir, "*.png")))
    if not images:
        return "추출된 이미지가 없습니다."

    lines = [f"🖼️ 논문 추출 이미지: {len(images)}개\n"]
    for img in images:
        lines.append(f"  • {os.path.basename(img)}")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8012)

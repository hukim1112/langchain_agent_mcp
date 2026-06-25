# =====================================================================
# MCP 변환 전 Retriever 모듈 테스트
#
# 사용법:
#   cd <프로젝트 루트>
#   python mcp/test_retrievers.py
#
# 다운로드한 rag_database/ 래퍼 모듈들이 정상 동작하는지 검증합니다.
#   1) bok_report  — 한국은행 보고서 Self-Querying (ChromaDB)
#   2) chinook_sql — Chinook 음악 DB Text2SQL (LangGraph)
#   3) paper_rag   — Modular RAG 논문 벡터 검색 (ChromaDB + MMR)
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

# ── 환경 설정 ──
load_dotenv(override=True)

# 이 스크립트는 mcp/ 폴더 안에 있으므로 한 단계 위가 프로젝트 루트
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
os.chdir(PROJECT_ROOT)

# rag_database 패키지를 import 하기 위해 mcp/ 를 sys.path에 추가
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

print(f"✅ Project Root: {PROJECT_ROOT}")
print(f"✅ MCP Directory: {SCRIPT_DIR}")


# ── 모듈 임포트 ──
from rag_database import bok_report, chinook_sql, paper_rag
from langchain_openai import OpenAIEmbeddings

print("✅ 모듈 임포트 성공\n")


# ── Retriever 초기화 ──
embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")

print("=" * 60)
print("📊 [1/3] 한국은행 보고서 Retriever 초기화")
print("=" * 60)
bok_report_search = bok_report.get_retriever(
    embedding_model=embedding_model,
    db_directory=os.path.join(SCRIPT_DIR, "report_db"),
)

print("\n" + "=" * 60)
print("🎵 [2/3] Chinook SQL Retriever 초기화")
print("=" * 60)
chinook_search = chinook_sql.get_retriever(
    model_name="gpt-4o",
    db_directory=os.path.join(SCRIPT_DIR, "sqlite", "Chinook.db"),
)

print("\n" + "=" * 60)
print("📄 [3/3] 논문 RAG Retriever 초기화")
print("=" * 60)
paper_search = paper_rag.get_retriever(
    db_directory=os.path.join(SCRIPT_DIR, "papers_rag"),
)

print("\n✅ 모든 Retriever 초기화 완료!\n")


# ── 검색 테스트 ──
def separator(title):
    print("\n" + "=" * 60)
    print(f"🔍 {title}")
    print("=" * 60)


# 1) 한국은행 보고서
separator("TEST 1 — 한국은행 보고서 Self-Querying")
query = "2024년 3분기 반도체 업종 동향 알려줘"
print(f"   쿼리: {query}\n")
results = bok_report_search.invoke(query)
print(f"   📄 검색 결과: {len(results)}건")
for i, doc in enumerate(results):
    print(f"\n   [{i+1}] 메타데이터: {doc.metadata}")
    print(f"       내용: {doc.page_content[:150]}...")


# 2) Chinook Text2SQL
separator("TEST 2 — Chinook DB Text2SQL")
query = "가장 많은 앨범을 산 고객은?"
print(f"   쿼리: {query}\n")
result = chinook_search.invoke({"question": query})
print(f"   📊 생성된 SQL: {result.get('query', 'N/A')}")
print(f"   💾 실행 결과:  {result.get('result', 'N/A')}")
print(f"   💬 최종 답변:  {result.get('answer', 'N/A')}")


# 3) 논문 RAG
separator("TEST 3 — Modular RAG 논문 검색")
query = "모듈러 RAG의 정의는?"
print(f"   쿼리: {query}\n")
results = paper_search.invoke(query)
print(f"   📄 검색 결과: {len(results)}건")
for i, doc in enumerate(results):
    source = doc.metadata.get("source", "unknown")
    print(f"\n   [{i+1}] Source: {source}")
    print(f"       내용: {doc.page_content[:150]}...")


print("\n" + "=" * 60)
print("✅ 모든 테스트 완료!")
print("   다음 단계: 이 검색기들을 FastMCP 서버로 래핑합니다.")
print("=" * 60)

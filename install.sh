#!/bin/bash

# 1. 시스템 패키지 설치 (Linux/Codespaces)
# PDF 처리 및 멀티모달 기능을 위해 시스템 레벨의 의존성이 필요합니다.
sudo apt-get update
sudo apt-get install -y poppler-utils

# 2. 필수 라이브러리 설치
pip install -r requirements.txt
pip install gdown

# 3. MCP 서버용 데이터 다운로드
# 한국은행 보고서 벡터스토어, Chinook SQLite DB, 논문 RAG 벡터스토어,
# LangChain retriever 래퍼 모듈을 Google Drive에서 다운로드합니다.
echo ""
echo "============================================"
echo "📂 MCP 데이터 다운로드를 시작합니다..."
echo "============================================"

MCP_DIR="$(dirname "$0")/mcp"
mkdir -p "$MCP_DIR"

echo "📊 [1/4] 한국은행 보고서 벡터스토어 다운로드 중..."
gdown --folder 1FeC55A3epRxPPWcdbZPPPMWG6YFEFWDR -O "$MCP_DIR/report_db"

echo "🎵 [2/4] Chinook SQLite 데이터베이스 다운로드 중..."
gdown --folder 1Ks0bOwqPRR0zAIUBsj8-Hwwdli37z_sl -O "$MCP_DIR/sqlite"

echo "📄 [3/4] 논문 RAG 벡터스토어 다운로드 중..."
gdown --folder 15ZvjFKlUuRk5u75IDv9EpQO7Hm2L1WZY -O "$MCP_DIR/papers_rag"

echo "🐍 [4/4] Retriever 모듈 다운로드 중..."
gdown --folder 1yhss1tfgTMGrVsEZ6PNgv3p0lEMOKywn -O "$MCP_DIR/rag_database"

echo ""
echo "============================================"
echo "✅ 설치 및 데이터 다운로드 완료!"
echo "============================================"

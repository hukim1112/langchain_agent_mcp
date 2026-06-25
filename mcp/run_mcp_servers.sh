#!/bin/bash
# =====================================================================
# MCP 서버 3종 일괄 실행 스크립트
#
# 사용법:
#   bash mcp/run_mcp_servers.sh         # 전체 실행
#   bash mcp/run_mcp_servers.sh stop    # 전체 중지
# =====================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# .env 로드
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

if [ "$1" = "stop" ]; then
    echo "🛑 MCP 서버 중지 중..."
    pkill -f "bok_server.py" 2>/dev/null && echo "  ✅ BOK Server 중지" || echo "  ⚠️ BOK Server 미실행"
    pkill -f "chinook_server.py" 2>/dev/null && echo "  ✅ Chinook Server 중지" || echo "  ⚠️ Chinook Server 미실행"
    pkill -f "papers_server.py" 2>/dev/null && echo "  ✅ Papers Server 중지" || echo "  ⚠️ Papers Server 미실행"
    exit 0
fi

echo "🚀 MCP 서버 3종을 시작합니다..."
echo ""

# 1. BOK Report Search Server
echo "📊 [1/3] BOK Report Search → http://localhost:8010/sse"
python "$SCRIPT_DIR/bok_server.py" &
sleep 2

# 2. Chinook Music DB Server
echo "🎵 [2/3] Chinook Music DB → http://localhost:8011/sse"
python "$SCRIPT_DIR/chinook_server.py" &
sleep 2

# 3. Papers RAG Search Server
echo "📄 [3/3] Papers RAG Search → http://localhost:8012/sse"
python "$SCRIPT_DIR/papers_server.py" &
sleep 2

echo ""
echo "============================================"
echo "✅ 모든 MCP 서버 실행 완료!"
echo ""
echo "   📊 BOK Reports:  http://localhost:8010/sse"
echo "   🎵 Chinook DB:   http://localhost:8011/sse"
echo "   📄 Papers RAG:   http://localhost:8012/sse"
echo ""
echo "   중지하려면: bash mcp/run_mcp_servers.sh stop"
echo "============================================"

# 포그라운드 유지 (Ctrl+C로 종료 시 모두 중지)
trap "echo '🛑 서버 중지...'; kill 0" SIGINT
wait

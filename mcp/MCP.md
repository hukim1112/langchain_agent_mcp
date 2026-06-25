# Available MCP Servers

이 프로젝트에서 사용 가능한 MCP 서버 목록입니다.
에이전트는 이 정보를 참고하여 적절한 서버에 연결하고 도구를 호출합니다.

## 서버 목록

| 서버명 | URL | 설명 | 주요 도구 |
|--------|-----|------|-----------|
| BOK Report Search | `http://localhost:8010/sse` | 한국은행 주력산업 모니터링 보고서 검색 | `query_bok_reports` |
| Chinook Music DB | `http://localhost:8011/sse` | Chinook 음악 데이터베이스 자연어 질의 | `query_chinook_database`, `get_chinook_schema` |
| Papers RAG Search | `http://localhost:8012/sse` | Modular RAG 논문 검색 | `query_papers`, `list_paper_images` |

## 사용 예시

- 한국은행 보고서 조회: "2024년 3분기 반도체 업종 동향 알려줘"
- Chinook DB 질의: "가장 매출이 높은 아티스트 5명을 알려줘"
- 논문 검색: "Modular RAG의 핵심 아키텍처를 설명해줘"

## 서버 실행 방법

```bash
bash mcp/run_mcp_servers.sh
```

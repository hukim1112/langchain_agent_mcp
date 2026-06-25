from .coder import create_coder_agent
from .utils import dynamic_response_format

# 🏭 에이전트 레지스트리 (Agent Registry)
# 새 에이전트 추가 시 여기에 정보 한 줄만 작성하면 서버, UI, CLI에 모두 반영됩니다.
AGENT_REGISTRY = [
    {
        "name": "supervisor",
        "module": "app.agents.supervisor",
        "prefix": "/supervisor",
        "tags": ["Supervisor"],
        "description": "전체 수집 프로세스를 조율하고 네비게이터와 코더를 지휘하는 감독 에이전트"
    },
    {
        "name": "mcp_agent",
        "module": "app.agents.mcp_agent",
        "prefix": "/mcp",
        "tags": ["MCP"],
        "description": "MCP 서버를 동적으로 탐색하고 호출하여 외부 데이터를 검색·분석하는 에이전트"
    },
    {
        "name": "coder",
        "module": "app.agents.coder",
        "prefix": "/coder",
        "tags": ["Coder"],
        "description": "수집 설계도를 바탕으로 수집 코드를 작성하고 자가 수정(Self-Healing)을 수행하는 코더 에이전트"
    },
    {
        "name": "chatbot",
        "module": "app.agents.chatbot",
        "prefix": "/chatbot",
        "tags": ["Chatbot"],
        "description": "도구 없이 자연어 대화만 수행하는 범용 AI 어시스턴트"
    }
]

__all__ = [
    "AGENT_REGISTRY",
    "create_coder_agent",
    "dynamic_response_format"
]

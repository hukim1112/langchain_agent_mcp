from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from app.prompts import MCP_AGENT_SYSTEM_PROMPT
from app.tools import tools_mcp


def create_mcp_agent(model_name: str = "google_genai:gemini-2.5-flash", temperature: float = 0.1):
    """MCP 서버를 동적으로 탐색·호출하는 MCP 연동 에이전트 생성"""
    model = init_chat_model(model_name, temperature=temperature)
    checkpointer = InMemorySaver()

    agent = create_agent(
        model=model,
        system_prompt=MCP_AGENT_SYSTEM_PROMPT,
        tools=tools_mcp,
        checkpointer=checkpointer,
        name="mcp_agent"
    )
    return agent


agent_executor = create_mcp_agent()

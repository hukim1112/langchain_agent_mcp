import sys
import os
import json

from langchain.tools import tool, ToolRuntime
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

# Load environment
from dotenv import load_dotenv
load_dotenv(override=True)

# 워커 에이전트들 임포트 — app/ 패키지 기반
from app.agents.coder import create_coder_agent
from app.schemas import SeniorCoderContext

# 추가 유틸리티 툴스 (Tool Factory)
from app.tools import tools_supervisor

# 서빙용 프롬프트
from app.prompts import SUPERVISOR_SYSTEM_PROMPT

# 하위 에이전트는 전역에서 한 번만 생성하고 재사용하여 메모리/맥락(Checkpointer)을 유지합니다.

# =========================================================
# 1. 하위 에이전트 인스턴스 전역 생성 (상태 유지용)
# =========================================================
GLOBAL_CODER_AGENT = create_coder_agent()

# =========================================================
# 2. 분리된(Context Isolated) Handoff 도구 (Agents as Tools 패턴)
# =========================================================
       
@tool(parse_docstring=True)
async def chat_to_coder(task_description: str, runtime: ToolRuntime, config: RunnableConfig) -> str:
    """Coder에게 파이썬 코드 작성, 실행, 디버깅 등의 작업을 지시할 때 사용합니다.
    
    Args:
        task_description: 작성할 스크립트의 코드 구현 목표 및 구체적 요구사항
    """
    
    prompt = f"다음 [Task]를 수행하세요.\n\n[Task]\n{task_description}"
        
    print(f"\n👨‍💼 [Supervisor] Coder와 대화 중...")
    
    inner_config = config.copy() if config else {}
    inner_config["configurable"] = inner_config.get("configurable", {}).copy()
    inner_config["configurable"]["thread_id"] = config.get("configurable", {}).get("thread_id", "default_thread")
    
    result = await GLOBAL_CODER_AGENT.ainvoke(
        {"messages": [("user", prompt)]},
        context=SeniorCoderContext(),
        config=inner_config
    )
    return result["messages"][-1].content


# =========================================================
# 3. Supervisor Agent 구성
# =========================================================

supervisor_model = init_chat_model("google_genai:gemini-2.5-pro", temperature=0.1)
supervisor_checkpointer = InMemorySaver()

supervisor_agent = create_agent(
    model=supervisor_model,
    system_prompt=SUPERVISOR_SYSTEM_PROMPT,
    tools=[chat_to_coder] + tools_supervisor,
    checkpointer=supervisor_checkpointer,
    name="supervisor_agent"
)

# app/server.py에서 agent_executor로 접근할 수 있게 alias 지정
agent_executor = supervisor_agent

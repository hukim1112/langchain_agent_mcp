import os
from typing_extensions import TypedDict, Annotated
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseLanguageModel
from langgraph.graph import START, StateGraph, END
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from typing import Optional

# --- (1) 워크플로우 상태(State) 정의 ---
# 그래프의 노드 간에 전달될 데이터 구조를 정의합니다.

class State(TypedDict):
    """
    LangGraph의 상태를 정의합니다.
    - question: 사용자의 원본 질문
    - query: 생성된 SQL 쿼리
    - result: SQL 쿼리 실행 결과
    - answer: LLM이 생성한 최종 답변
    """
    question: str
    query: str
    result: str
    answer: str

class QueryOutput(TypedDict):
    """SQL 쿼리 생성을 위한 구조화된 출력(Structured Output) 정의"""
    query: Annotated[str, ..., "문법적으로 올바른 SQL 쿼리"]


# --- (2) 쿼리 생성용 프롬프트 템플릿 정의 ---
# (이 프롬프트들은 정적이므로 함수 외부에 선언해도 됩니다)

system_message = """
입력된 질문을 받아서, 정답을 찾는 데 도움이 되는 문법적으로 올바른 {dialect} 쿼리를 작성하세요.
사용자가 질문에서 얻고자 하는 결과 개수를 명시하지 않는 한, 항상 최대 {top_k} 개의 결과만 반환하도록 쿼리를 제한하세요.
또한 결과를 데이터베이스에서 가장 흥미로운 예시가 나오도록 적절한 컬럼으로 정렬할 수 있습니다.

특정 테이블에서 모든 컬럼을 조회하지 말고, 질문과 관련된 몇 개의 컬럼만 요청하세요.

스키마 설명에서 확인할 수 있는 컬럼 이름만 사용해야 합니다. 존재하지 않는 컬럼을 조회하지 않도록 주의하세요.
또한 어떤 컬럼이 어느 테이블에 속하는지도 주의해야 합니다.

다음 테이블만 사용하세요:
{table_info}
"""

user_prompt = "질문: {input}"

query_prompt_template = ChatPromptTemplate(
    [("system", system_message), ("user", user_prompt)]
)


# --- (3) 메인 함수: 워크플로우 그래프 생성 ---

def get_retriever(
    model_name: str, 
    db_directory: str, 
    temperature: float = 0):
    """
    SQL Text-to-SQL 워크플로우를 캡슐화하는 LangGraph를 생성하고 컴파일하여 반환합니다.
    모델 이름과 DB 경로를 입력받아 내부에서 객체를 초기화합니다.

    Args:
        model_name: 쿼리 생성 및 답변 생성에 사용할 LLM 모델 이름 (예: "gpt-4o").
        db_path: 쿼리를 실행할 SQLite 데이터베이스 파일 경로 (예: "./db/Chinook.db").
        temperature: LLM의 temperature.

    Returns:
        컴파일된 LangGraph (app) 객체.
        초기화 실패 시 None을 반환합니다.
    """
    
    # --- (A) LLM 및 DB 객체 초기화 ---
    
    # (필수) OPENAI_API_KEY 환경 변수 확인
    if "OPENAI_API_KEY" not in os.environ:
        print("Error: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        return None
        
    try:
        llm = ChatOpenAI(model=model_name, temperature=temperature)
    except Exception as e:
        print(f"Error initializing LLM ({model_name}): {e}")
        print("OPENAI_API_KEY가 올바르게 설정되었는지 다시 확인하세요.")
        return None

    if not os.path.exists(db_directory):
        print(f"Error: Database file not found at: {db_directory}")
        print("db_directory 인자가 올바른지 확인하세요.")
        return None
        
    try:
        db = SQLDatabase.from_uri(f"sqlite:///{db_directory}")
    except Exception as e:
        print(f"Error connecting to database at {db_directory}: {e}")
        return None

    print(f"LLM({model_name}) 및 DB({db_directory}) 초기화 성공.")

    # --- (B) 그래프 노드(Node) 함수 정의 ---
    #
    # 이 함수들은 'create_sql_workflow_graph' 내부에 정의되어
    # 위에서 생성된 'llm'과 'db' 변수에 접근할 수 있습니다.
    
    def write_query(state: State):
        """(노드 1) 정보를 가져오기 위한 SQL 쿼리를 생성"""
        print("--- [Graph] 1. SQL 쿼리 생성 중... ---")
        
        prompt = query_prompt_template.invoke(
            {
                "dialect": db.dialect,
                "top_k": 10,
                "table_info": db.get_table_info(),
                "input": state["question"],
            }
        )
        
        structured_llm = llm.with_structured_output(QueryOutput)
        result = structured_llm.invoke(prompt)
        
        print(f"--- [Graph] 생성된 쿼리: {result['query']} ---")
        return {"query": result["query"]}

    def execute_query(state: State):
        """(노드 2) SQL 쿼리를 실행"""
        print("--- [Graph] 2. SQL 쿼리 실행 중... ---")
        
        execute_query_tool = QuerySQLDatabaseTool(db=db)
        
        try:
            query_result = execute_query_tool.invoke(state["query"])
        except Exception as e:
            print(f"--- [Graph] 쿼리 실행 오류: {e} ---")
            query_result = f"Error executing query: {e}"
            
        print(f"--- [Graph] 실행 결과: {query_result} ---")
        return {"result": str(query_result)}

    def generate_answer(state: State):
        """(노드 3) DB 정보를 바탕으로 최종 답변 생성"""
        print("--- [Graph] 3. 최종 답변 생성 중... ---")

        prompt = (
            "다음의 사용자 질문, 해당 SQL 쿼리, 그리고 SQL 실행 결과를 참고하여 "
            "사용자의 질문에 답변하세요.\n\n"
            f"질문: {state['question']}\n"
            f"SQL 쿼리: {state['query']}\n"
            f"SQL 결과: {state['result']}"
        )

        response = llm.invoke(prompt)
        print(f"--- [Graph] 생성된 답변: {response.content} ---")
        return {"answer": response.content}

    # --- (C) 그래프 구성 및 컴파일 ---
    
    graph_builder = StateGraph(State)

    graph_builder.add_sequence(
        [write_query, execute_query, generate_answer]
    )
    
    graph_builder.add_edge(START, "write_query")

    print("SQL 워크플로우 그래프 컴파일 완료.")
    graph_app = graph_builder.compile()
    
    return graph_app


# --- (4) 이 파일이 직접 실행될 때의 테스트 코드 ---
if __name__ == "__main__":
    
    # (필수) OPENAI_API_KEY 환경 변수 설정
    if "OPENAI_API_KEY" not in os.environ:
        print("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        # os.environ["OPENAI_API_KEY"] = "sk-..." # 여기에 키를 입력
    
    # (필수) Chinook.db 파일 경로 설정
    PATH_TO_DB = "/content/sqlite/Chinook.db" # ⬅️ ★★★ 이 경로를 수정하세요 ★★★

    # API 키가 있고 DB 경로가 존재할 때만 테스트 실행
    if "OPENAI_API_KEY" in os.environ:
        
        print("테스트 실행: create_sql_workflow_graph 함수를 호출합니다.")
        
        # 1. 메인 함수를 호출하여 그래프 'app'을 가져옵니다.
        #    (이제 문자열 인자를 전달합니다)
        sql_graph_app = get_retriever(
            model_name="gpt-4o", 
            db_path=PATH_TO_DB
        )
        
        # 2. 그래프가 성공적으로 생성되었는지 확인
        if sql_graph_app:
            print("\n--- 그래프 생성 성공 ---")
            
            # 3. 생성된 'app'을 테스트합니다.
            test_question = "직원의 수는 얼마나 있어?"
            print(f"\n--- 테스트 질문: '{test_question}' ---")
            
            inputs = {"question": test_question}
            final_state = sql_graph_app.invoke(inputs)
            
            print("\n--- 최종 상태(Final State) ---")
            import pprint
            pprint.pprint(final_state)
            
            print("\n--- 최종 답변 ---")
            print(final_state.get("answer", "답변을 찾을 수 없습니다."))
        
        else:
            print("\n--- [오류] 그래프 생성 실패 ---")
            print("OPENAI_API_KEY 또는 PATH_TO_DB 경로를 확인하세요.")
            
    else:
        print("\n[오류] OPENAI_API_KEY 환경 변수를 설정하고 테스트를 다시 실행하세요.")


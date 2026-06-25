from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain_classic.chains.query_constructor.schema import AttributeInfo
from langchain_classic.retrievers.self_query.base import SelfQueryRetriever
from langchain_core.embeddings import Embeddings
from typing import Optional

def get_retriever(
    embedding_model: Embeddings,
    db_directory: str = "./report_db",
    collection_name: str = "bok_industry_report",
    model_name: str = "gpt-4o",
    temperature: float = 0
) -> SelfQueryRetriever:
    """
    한국은행 산업 보고서용 SelfQueryRetriever를 초기화하고 반환합니다.

    Args:
        embedding_model: 사용할 임베딩 모델 객체. (필수)
                         이 모델은 DB를 생성할 때 사용한 모델과 동일해야 합니다.
        db_directory: Chroma DB의 영구 저장 디렉토리.
        collection_name: Chroma 컬렉션 이름.
        model_name: Self-query LLM으로 사용할 모델 이름. (gpt-4o 권장)
        temperature: LLM의 temperature.

    Returns:
        SelfQueryRetriever 객체.
    """
    
    # 1. 디스크에서 벡터 저장소 로드
    # 참고: 최신 LangChain에서는 `embedding` 대신 `embedding_function` 매개변수를 사용합니다.
    try:
        report_vectorstore = Chroma(
            embedding_function=embedding_model, 
            persist_directory=db_directory,
            collection_name=collection_name
        )
    except Exception as e:
        print(f"Error loading vector store from {db_directory}: {e}")
        print("Please ensure the Chroma DB directory exists and was created with the same embedding model.")
        raise

    # 2. 메타데이터 필드 정보 정의
    metadata_field_info = [
        AttributeInfo(
            name="year",
            description="해당 보고서의 연도를 나타내는 정수 값 (예: 2024)",
            type="integer",
        ),
        AttributeInfo(
            name="quarter",
            description="해당 보고서의 분기를 나타내는 숫자로 1, 2, 3, 4 중 하나.",
            type="integer",
        ),
    ]

    # 3. 문서 내용 설명
    document_content_description = (
        "한국은행에서 발간한 한국의 주요 8대 업종 분기별 동향 보고서. "
        "IMPORTANT: Filter values for 'year' and 'quarter' must always be "
        "integers (e.g., 2024, 1), NEVER strings (e.g., \"2024\", \"1\")."
    )

    # 4. LLM 초기화
    llm = ChatOpenAI(model=model_name, temperature=temperature)

    # 5. SelfQueryRetriever 생성 및 반환
    sq_retriever = SelfQueryRetriever.from_llm(
        llm,
        report_vectorstore,
        document_content_description,
        metadata_field_info,
        verbose=True # 디버깅을 위해 Self-query 과정을 로그로 출력
    )
    
    return sq_retriever

# --- 이 파일이 직접 실행될 때 간단한 테스트 코드 ---
if __name__ == "__main__":
    # 이 테스트를 실행하려면 OPENAI_API_KEY가 환경 변수로 설정되어 있어야 합니다.
    # 또한 `langchain_openai`에서 `OpenAIEmbeddings`를 임포트해야 합니다.
    try:
        from langchain_openai import OpenAIEmbeddings
        
        # 1. 임베딩 모델 초기화 (★중요★)
        # 사용자의 원래 코드에 있던 `embedding_model` 객체를 사용해야 합니다.
        # 여기서는 OpenAIEmbeddings를 예시로 사용합니다.
        print("Initializing embedding model (example)...")
        embeddings = OpenAIEmbeddings() 
        
        # 2. 리트리버 가져오기
        print("Getting retriever...")
        retriever = get_retriever(embedding_model=embeddings)
        
        print("\nRetriever created successfully.")

        # 3. 간단한 쿼리 테스트
        print("\nTesting retriever with query '2024년 1분기 보고서'...")
        # SelfQueryRetriever는 .invoke()를 사용합니다.
        results = retriever.invoke("2024년 1분기 보고서 찾아줘")
        
        print(f"\nFound {len(results)} documents:")
        for doc in results:
            print(f"- Metadata: {doc.metadata}")
            print(f"  Content: {doc.page_content[:70]}...")

    except ImportError:
        print("Please install langchain_openai to run this test.")
    except Exception as e:
        print(f"\n--- An error occurred during test ---")
        print(f"{e}")
        print("Ensure your OPENAI_API_KEY is set and Chroma DB exists at './report_db'.")

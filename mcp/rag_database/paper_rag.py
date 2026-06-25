import os
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.vectorstores import VectorStoreRetriever

def get_retriever(
    db_directory: str = "./papers_rag",  # 앞서 생성한 DB 경로
    collection_name: str = "modular_rag",    # 앞서 지정한 컬렉션 이름
    k: int = 5  # 검색할 문서 청크 개수
) -> VectorStoreRetriever:
    """
    저장된 Chroma DB에서 Modular RAG 논문 검색기를 로드합니다.
    
    Args:
        db_directory: Chroma DB가 저장된 폴더 경로
        collection_name: 컬렉션 이름
        k: 검색할 문서의 개수 (Top-k)

    Returns:
        VectorStoreRetriever: 검색기 객체
    """
    
    # 1. 임베딩 모델 준비 
    # (DB 생성 때와 동일한 모델이어야 함)
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")

    # 2. 디스크에서 벡터 저장소 로드
    if not os.path.exists(db_directory):
        raise FileNotFoundError(f"❌ DB 디렉토리를 찾을 수 없습니다: {db_directory}")

    try:
        vectorstore = Chroma(
            embedding_function=embedding_model, 
            persist_directory=db_directory,
            collection_name=collection_name
        )
        print(f"✅ Vectorstore 로드 성공: {db_directory} (Collection: {collection_name})")
    except Exception as e:
        print(f"❌ Vectorstore 로드 실패: {e}")
        raise

    # 3. Retriever 생성
    # search_type="mmr": 유사하면서도 서로 다른 내용을 다양하게 가져옴 (중복 방지)
    # search_kwargs={"k": k}: 상위 k개 문서 검색
    retriever = vectorstore.as_retriever(
        search_type="mmr", 
        search_kwargs={"k": k, "fetch_k": k*2} 
    )
    
    return retriever

# --- 테스트 코드 ---
if __name__ == "__main__":
    try:
        # 1. 리트리버 가져오기
        retriever = get_retriever()
        
        # 2. 테스트 쿼리
        test_query = "Modular RAG의 정의가 뭐야?"
        print(f"\n🔍 테스트 검색: '{test_query}'")
        
        results = retriever.invoke(test_query)
        
        print(f"📄 검색된 문서 개수: {len(results)}개")
        for i, doc in enumerate(results):
            print(f"\n[Result {i+1}] Source: {doc.metadata.get('source', 'unknown')}")
            print("-" * 50)
            print(doc.page_content[:150] + "...") # 앞부분만 출력
            
            # 이미지 경로가 있는지 확인 (멀티모달 RAG 핵심)
            if "extracted_images" in doc.page_content:
                print("🖼️ (이 문서에는 이미지가 포함되어 있습니다)")

    except Exception as e:
        print(f"\n⚠️ 테스트 중 오류 발생: {e}")
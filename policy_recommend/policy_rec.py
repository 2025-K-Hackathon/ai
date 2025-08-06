import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain_community.embeddings import SentenceTransformerEmbeddings
from dotenv import load_dotenv

# 검색된 문서(Document 객체)들을 하나의 깔끔한 문자열로 합치는 함수
def format_docs(docs):
    return "\n\n".join(f"정책 제목: {doc.metadata.get('title', '제목 없음')}\n내용: {doc.page_content}" for doc in docs)

def get_age(birth_year):
    age = 2025 - birth_year
    return age

def main():
    load_dotenv()

    try:
        API_KEY = os.getenv("API_KEY")
        MODEL_ID = os.getenv("MODEL_ID")
        API_BASE = os.getenv("API_BASE")
        if not API_KEY or not MODEL_ID or not API_BASE:
            raise KeyError
    except KeyError:
        print("오류: .env 파일에 API_KEY, MODEL_ID, API_BASE를 설정해야 합니다.")
        exit()

    # 테스트할 가상 사용자 프로필 정의
    sample_user_profile = {
        "name": "린 응우엔",
        "nationality": "베트남",
        "age": get_age(1998),
        "region": "서울",
        "marriage_status": "기혼",
        "has_child": True,
        "child_age": get_age(2020),
    }
    print("1. 테스트 사용자 프로필:")
    print(sample_user_profile)

    DB_DIRECTORY = "./policy_chroma_db"
    if not os.path.exists(DB_DIRECTORY):
        print(f"오류: '{DB_DIRECTORY}' 데이터베이스 폴더를 찾을 수 없습니다.")
        return
        
    print("로컬 임베딩 모델을 로드합니다...")
    embeddings = SentenceTransformerEmbeddings(
        model_name="jhgan/ko-sbert-nli"
    )
    
    db = Chroma(persist_directory=DB_DIRECTORY, embedding_function=embeddings)
    print("\n2. ChromaDB 로드 완료!")

    search_regions = ["전국", sample_user_profile["region"]]
    
    metadata_filter = {
        "region": {"$in": search_regions}
    }
    
    query_text = f"""{sample_user_profile['name']}은 {sample_user_profile['nationality']} 국적의 {sample_user_profile['age']}세 부모입니다.
    현재 {sample_user_profile['region']}에 거주하며, 만 {sample_user_profile['child_age']}세 자녀를 둔 어머니입니다."""
    
    print(f"\n3. 생성된 AI 검색어: \"{query_text}\"")
    print(f"   적용된 DB 필터: {metadata_filter}")
    
    # DB에서 필터와 검색어에 맞는 문서를 찾아오는 retriever 설정
    retriever = db.as_retriever(
        search_type="similarity",
        search_kwargs={'k': 3, 'filter': metadata_filter}
    )
    
    llm = ChatOpenAI(
        model_name=MODEL_ID,
        openai_api_key=API_KEY,
        openai_api_base=API_BASE,
        model_kwargs={"temperature": 0.5, "max_tokens": 1024}
    )
    
    prompt = ChatPromptTemplate.from_template("""
    You are a kind and competent policy recommendation AI for the 'Dajeong' service.
    Based on the user's situation and the provided context, find the most helpful policies, list up to a maximum of 3 in order of recommendation, and briefly summarize the key points.
    You must explain the reason for the recommendation in a gentle tone and summarize the key policy content in an easy-to-understand way.

    Your mission is to answer ONLY based on the information found within the provided 'Context'.
    You must NEVER mention, guess, or create information that is not explicitly stated in the 'Context'.
    If the 'Context' contains no relevant information for the user's situation, you must honestly reply with the exact following Korean sentence: "죄송하지만, 현재 사용자님의 상황에 꼭 맞는 정책 정보를 찾지 못했습니다."

    [Context]
    {context}

    [User Situation]
    {question}

    [Personalized Policy Recommendation Based on Context]
    """)
    
    rag_chain = RunnableParallel(
        answer=(
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        ),
        source_documents=retriever, #  retriever를 통해 찾은 원본 문서를 그대로 반환
    )
    
    print("\n4. RAG Chain 준비 완료. 이제 AI에게 정책 추천을 요청합니다...")

    response = rag_chain.invoke(query_text)
    
    print("\n" + "="*40)
    print("           AI의 최종 맞춤 정책 추천 결과")
    print("="*40)
    print(response["answer"])
    print("\n" + "="*40)
    print("              답변 생성에 참고한 원본 문서")
    print("="*40)
    
    for doc in response["source_documents"]:
        print(f"출처: {doc.metadata.get('source')}, 제목: {doc.metadata.get('title')}")

if __name__ == "__main__":
    main()
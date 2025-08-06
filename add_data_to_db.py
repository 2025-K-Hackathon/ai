import os
import shutil
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from dotenv import load_dotenv

from load_data_to_db import load_and_process_json

# 이미 존재하는 ChromaDB에 새로운 JSON 파일의 내용을 추가하는 메인 함수
def main():
    load_dotenv()
    API_KEY = os.getenv("API_KEY")
    MODEL_ID = os.getenv("MODEL_ID")
    API_BASE = os.getenv("API_BASE")
    if not API_KEY or not MODEL_ID or not API_BASE:
        print("오류: .env 파일에 API_KEY, MODEL_ID, API_BASE를 설정해야 합니다.")
        return

    # 지역 정보 추출에 사용할 LLM
    extraction_llm = ChatOpenAI(model_name=MODEL_ID, openai_api_key=API_KEY, openai_api_base=API_BASE, temperature=0)
    
    # 추가할 새로운 JSON 파일 경로
    NEW_JSON_FILE_PATH = "crawling/타기관_notices_2025.json"
    if not os.path.exists(NEW_JSON_FILE_PATH):
        print(f"오류: 추가할 파일 '{NEW_JSON_FILE_PATH}'을 찾을 수 없습니다.")
        return

    DB_DIRECTORY = "./policy_chroma_db"
    if not os.path.exists(DB_DIRECTORY):
        print(f"오류: 기존 데이터베이스 폴더 '{DB_DIRECTORY}'를 찾을 수 없습니다.")
        print("load_data_to_db.py를 먼저 실행하여 데이터베이스를 생성해주세요.")
        return
    
    embeddings = SentenceTransformerEmbeddings(model_name="jhgan/ko-sbert-nli")

    print(f"1. 새로운 데이터 로드 및 전처리 시작: {NEW_JSON_FILE_PATH}")
    new_documents = load_and_process_json(NEW_JSON_FILE_PATH, extraction_llm)
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    new_split_docs = text_splitter.split_documents(new_documents)
    print(f"2. 텍스트 분할 완료! (총 {len(new_split_docs)}개의 새 조각)")

    print("\n3. 기존 ChromaDB 로드 및 새로운 데이터 추가 시작...")
    
    db = Chroma(
        persist_directory=DB_DIRECTORY, 
        embedding_function=embeddings
    )
    
    db.add_documents(new_split_docs)
    
    print(f"4. 데이터 추가 완료! ({DB_DIRECTORY}가 업데이트되었습니다.)")

if __name__ == "__main__":
    main()
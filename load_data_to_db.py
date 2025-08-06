import os
import json
import shutil
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# --- AI를 사용해 텍스트에서 지역 정보 추출하는 함수 ---
def extract_region_with_ai(text_content: str, llm: ChatOpenAI) -> str:
    prompt = f"""
    다음 텍스트 내용에서 언급된 대한민국의 핵심 지역(특별시, 광역시, 도 단위)을 하나만 찾아줘.
    만약 특정 지역이 언급되지 않거나 여러 지역이 언급되면 "전국"이라고만 답해줘. 다른 설명은 붙이지 마.

    텍스트: "{text_content[:500]}"

    지역:
    """
    try:
        response = llm.invoke(prompt)
        region = response.content.strip()
        if "서울" in region or "인천" in region or "경기" in region:
            return "수도권"
            
        elif "대전" in region or "세종" in region or "충남" in region or "충북" in region:
            return "충청도"
            
        elif "부산" in region or "대구" in region or "울산" in region or "경북" in region or "경남" in region:
            return "경상도"
            
        elif "광주" in region or "전남" in region or "전북" in region:
            return "전라도"
            
        elif "강원" in region:
            return "강원도"
            
        elif "제주" in region:
            return "제주도"
            
        else:
            return "전국"
    except Exception:
        return "전국"
    
    

def load_and_process_json(file_path: str, llm: ChatOpenAI) -> list:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    all_documents = []
    print(f"\n총 {len(data)}개의 정책에 대해 지역 정보 추출을 시작합니다.")
    
    for i, policy in enumerate(data):
        title = policy.get('title', '')
        print(f"  ({i+1}/{len(data)}) '{title}' 처리 중...")

        soup = BeautifulSoup(policy.get('content_html', ''), 'html.parser')
        main_content = soup.get_text(separator='\n', strip=True)
        attachment_texts = [f"첨부파일: {att.get('name', '')}" for att in policy.get('attachments', [])]
        full_content = main_content + "\n\n" + "\n".join(attachment_texts)

        text_for_region_extraction = title + "\n" + main_content
        extracted_region = extract_region_with_ai(text_for_region_extraction, llm)
        print(f"    -> 추출된 지역: {extracted_region}")

        metadata = {
            "source": file_path,
            "title": title,
            "date": policy.get('date', ''),
            "region": extracted_region,
            "attachment_urls": ", ".join([att.get('url', '') for att in policy.get('attachments', [])])
        }

        doc = Document(page_content=full_content, metadata=metadata)
        all_documents.append(doc)
    
    return all_documents

def main():
    load_dotenv()
    API_KEY = os.getenv("API_KEY")
    MODEL_ID = os.getenv("MODEL_ID")
    API_BASE = os.getenv("API_BASE")
    if not API_KEY or not MODEL_ID or not API_BASE:
        print("오류: .env 파일에 API_KEY, MODEL_ID, API_BASE를 설정해야 합니다.")
        return

    extraction_llm = ChatOpenAI(model_name=MODEL_ID, openai_api_key=API_KEY, openai_api_base=API_BASE, temperature=0)

    JSON_FILE_PATH = "crawling/notices_2025.json"
    if not os.path.exists(JSON_FILE_PATH):
        print(f"오류: '{JSON_FILE_PATH}' 파일을 찾을 수 없습니다.")
        return
    
    DB_DIRECTORY = "./policy_chroma_db"

    # # 기존 DB 폴더 삭제 - 새로 만들기 위함
    # if os.path.exists(DB_DIRECTORY):
    #     print(f"기존 데이터베이스 폴더 '{DB_DIRECTORY}'를 삭제합니다.")
    #     shutil.rmtree(DB_DIRECTORY)

    documents = load_and_process_json(JSON_FILE_PATH, extraction_llm)
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = text_splitter.split_documents(documents)
    print(f"\n텍스트 분할 완료! (총 {len(split_docs)}개 조각)")

    print("\n로컬 임베딩 모델 로딩 시작...")
    embeddings = SentenceTransformerEmbeddings(model_name="jhgan/ko-sbert-nli")
    print("로컬 임베딩 모델 로딩 완료!")
    
    print("\n임베딩 및 ChromaDB 저장 시작...")
    db = Chroma.from_documents(split_docs, embeddings, persist_directory=DB_DIRECTORY)
    print(f"ChromaDB 저장 완료! ({DB_DIRECTORY} 폴더를 확인하세요)")

if __name__ == "__main__":
    main()
import os
from typing import List
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

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


# AI가 반환할 답변의 구조
class DiaryAnalysisWithDiff(BaseModel):
    incorrect_words: List[str] = Field(description="원본 일기에서 맞춤법이나 문법이 틀렸던 단어들의 리스트")
    corrected_words: List[str] = Field(description="틀린 단어들을 올바르게 수정한 단어들의 리스트")
    full_corrected_text: str = Field(description="사용자의 원본 일기 전체를 자연스럽게 수정한 문장")
    reply: str = Field(description="수정된 일기 내용을 바탕으로 작성된, 짧고 따뜻한 공감의 답글")

# 사용자의 일기 내용을 받아 맞춤법 교정, 틀린 단어/고친 단어 분석, 공감 답글을 생성
def analyze_diary_entry(diary_text: str) -> dict:
    
    llm = ChatOpenAI(
        model_name=MODEL_ID,
        openai_api_key=API_KEY,
        openai_api_base=API_BASE,
        model_kwargs={"temperature": 0.7, "max_tokens": 1024}
    )
    
    parser = JsonOutputParser(pydantic_object=DiaryAnalysisWithDiff)

    prompt_template = """
    You are an AI counselor for the 'Dajeong' service and a competent Korean proofreader.
    Analyze the diary entry written by a married immigrant woman. You must respond strictly in JSON format according to the following six instructions.

    [Instructions]
    From the 'Original Diary', correct any awkward expressions, typos, and grammatical errors into a natural Korean sentence, and generate it as full_corrected_text.
    Based on the corrected content, write a short, warm reply of 1-3 sentences that empathizes with the user's emotions and offers comfort and encouragement. Generate this as reply.
    
    Find the words that were incorrect in the original diary and put them, in order, into the incorrect_words list.
    Put the corrected versions of those words into the corrected_words list.
    The incorrect_words and corrected_words lists must have the exact same number of items and correspond in order.
    If there are no incorrect words, return empty lists ([]) for incorrect_words and corrected_words.

    {format_instructions}

    [Original Diary]
    {diary_entry}
    """
    
    prompt = ChatPromptTemplate.from_template(
        template=prompt_template,
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    # LangChain 모든 요소 연결
    chain = prompt | llm | parser

    # 체인 실행
    print("AI가 일기를 분석하고 있습니다...")
    try:
        result = chain.invoke({"diary_entry": diary_text})
        return result
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        return None

if __name__ == "__main__":
    # 테스트
    sample_diary = "오늘 아이가 학교에서 친구랑 싸워따. 내가 한국말이 서툴어서 선생님한테 똑빠로 설명도 못해주고. 정말 답답했다. 나는 나쁜 엄마인것같다."
    
    print("=" * 30)
    print(f"입력된 일기: {sample_diary}")
    print("=" * 30)
    
    analysis_result = analyze_diary_entry(sample_diary)
    
    if analysis_result:
        print("\n[전체 리턴 결과]")
        print(analysis_result)
        print("=" * 30)

        # analysis_result 예시 결과
        # {'incorrect_words': ['똑빠로', '싸워따'], 'corrected_words': ['또박또박', '싸웠다'], 
        # 'full_corrected_text': '오늘 아이가 학교에서 친구랑 싸웠다. 내가 한국말이 서툴러서 ... 힘내세요!'}


        # print("\n[AI 분석 결과]")
        # print("-" * 30)
        # print(f"틀린 단어: {analysis_result['incorrect_words']}")
        # print(f"수정된 단어: {analysis_result['corrected_words']}")
        # print("-" * 30)
        # print(f"전체 교정 문장: {analysis_result['full_corrected_text']}")
        # print("-" * 30)
        # print(f"AI 답글: {analysis_result['reply']}")
        # print("-" * 30)
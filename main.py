import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from diary_ai.diary_ai_main import analyze_diary_entry
from policy_recommend.policy_rec import get_policy_recommendations
from TTS_gen.tts_generator import create_and_upload_tts as create_korean_tts

app = FastAPI()

# 입력 데이터 형식을 Pydantic으로 정의
class DiaryInput(BaseModel):
    diary_text: str

class UserProfile(BaseModel):
    name: str
    nationality: str
    age: int
    childAge: Optional[int] = None
    region: str
    married: bool
    hasChildren: bool

class TTSInput(BaseModel):
    text: str

# API 엔드포인트(라우터) 정의
@app.post("/api/v1/diary/analyze")
# 일기 내용을 받아 AI 분석을 수행하고 결과를 반환하는 API
def handle_diary_analysis(request: DiaryInput):
    diary_text = request.diary_text
    result = analyze_diary_entry(diary_text)
    return result

@app.post("/api/v1/policy/recommend")
# 사용자 프로필을 받아 맞춤형 정책을 추천하는 API
def recommend_policies_for_user(user_profile: UserProfile):
    profile_dict = user_profile.dict()
    result = get_policy_recommendations(profile_dict)
    return result

@app.post("/api/v1/tts/generate")
# 한국어 텍스트를 받아 TTS 오디오 파일을 생성하고 결과를 반환하는 API
def handle_tts_generation(request: TTSInput):
    korean_text = request.text
    output_filename = f"{hash(korean_text)}.mp3"
    
    success = create_korean_tts(text=korean_text, filename=output_filename)
    
    if success:
        return {"status": "success", "url": success}
    else:
        return {"status": "error", "message": "TTS 파일 생성에 실패했습니다."}

# 4. 서버 실행
if __name__ == "__main__":
    # uvicorn.run("파일이름:app객체이름", ...)
    # uvicorn main:app --reload
    # http://127.0.0.1:8000/docs 에서 테스트 가능
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
import os
from gtts import gTTS

def create_korean_tts(text: str, filename: str, output_dir: str = "tts_audio") -> bool:
    try:
        if not duplicate_tts(text, filename):
            tts = gTTS(text=text, lang='ko')
            
            save_path = os.path.join(output_dir, filename)
            tts.save(save_path)
            
            print(f"mp3 생성 성공: '{save_path}'")
            return True
        else:
            print(f"중복 파일: '{filename}', 이미 존재하는 파일입니다. 생성을 중단합니다.")
            return False
        
    except Exception as e:
        print(f"오디오 파일 생성 중 오류가 발생했습니다: {e}")
        return False

# 중복 파일 생성 방지 -> 중복이면 True 반환
def duplicate_tts(text: str, filename: str) -> bool:
    if os.path.exists(filename):
        
        return True
    else:
        return False
        
if __name__ == "__main__":
    sample_korean_text = "진료 예약하고 싶어요."
    output_filename = "appointment_request.mp3"
    
    print("=" * 30)
    print(f"변환할 텍스트: '{sample_korean_text}'")
    print("=" * 30)
    
    success = create_korean_tts(text=sample_korean_text, filename=output_filename, output_dir="tts_audio")
    
    if duplicate_tts(sample_korean_text, output_filename) and success:
        print(f"'tts_audio' 폴더 안에 '{output_filename}' 파일 생성 완료")
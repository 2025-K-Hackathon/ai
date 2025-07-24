import io
from typing import List, Tuple, Union, Optional
from google.cloud import storage
from google.cloud import texttospeech

BUCKET_NAME = 'dajeong-tts-audio'
KEY_PATH = './dj-tts-gcp-key.json'

storage_client = storage.Client.from_service_account_json(KEY_PATH)
tts_client = texttospeech.TextToSpeechClient.from_service_account_json(KEY_PATH)

# Google Cloud TTS로 오디오를 생성하여 바로 GCP Cloud Storage에 업로드
def create_and_upload_tts(text: str, filename: str, bucket_name: str) -> Optional[str]:
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        
        if blob.exists():
            print(f"중복 파일: GCP 버킷 '{bucket_name}'에 '{filename}'이(가) 이미 존재합니다.")
            return blob.public_url

        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code="ko-KR", 
            name="ko-KR-Standard-A"
            # "ko-KR-Wavenet-A" (표준 여성 WaveNet 목소리)
        )

        # 오디오 파일 형식 - MP3
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        print("음성 변환 요청 중...")
        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        print(f"'{filename}'을(를) GCP 버킷 '{bucket_name}'에 업로드하는 중...")
        # 응답받은 오디오 데이터를 바로 업로드
        blob.upload_from_string(response.audio_content, content_type='audio/mpeg')
        
        public_url = blob.public_url
        print(f"업로드 성공! 공개 URL: {public_url}")
        
        return public_url
        
    except Exception as e:
        print(f"오디오 생성 또는 업로드 중 오류가 발생했습니다: {e}")
        return None

# 여러 텍스트를 배치로 TTS 변환하여 GCP Cloud Storage에 업로드
def create_and_upload_tts_batch(samples: List[Tuple[str, str]], bucket_name: str) -> List[Tuple[str, str, Optional[str]]]:
    results = []
    
    print(f"총 {len(samples)}개의 텍스트를 배치 처리합니다...")
    
    for i, (text, filename) in enumerate(samples, 1):
        print(f"\n[{i}/{len(samples)}] 처리 중...")
        print("=" * 30)
        print(f"변환할 텍스트: '{text}'")
        
        url = create_and_upload_tts(text=text, filename=filename, bucket_name=bucket_name)
        results.append((text, filename, url))
        
        if url:
            print(f"-> 최종 결과물(URL): {url}")
        else:
            print("-> 생성 또는 업로드에 실패했거나, 파일이 이미 존재합니다.")
    
    # 배치 처리 결과 요약
    success_count = sum(1 for _, _, url in results if url is not None)
    print(f"\n{'='*50}")
    print(f"배치 처리 완료: {success_count}/{len(samples)} 성공")
    print(f"{'='*50}")
    
    return results

# 단일 텍스트 또는 여러 텍스트 처리
def create_and_upload_tts_flexible(*args, **kwargs) -> Union[Optional[str], List[Tuple[str, str, Optional[str]]]]:
    """
    사용법
    - 단일 텍스트: create_and_upload_tts_flexible("안녕하세요", "hello.mp3", bucket_name="my-bucket")
    - 여러 텍스트: create_and_upload_tts_flexible([("안녕하세요", "hello.mp3"), ("감사합니다", "thanks.mp3")], bucket_name="my-bucket")
    """
    if len(args) == 1 and isinstance(args[0], list):
        samples = args[0]
        bucket_name = kwargs.get('bucket_name', BUCKET_NAME)
        return create_and_upload_tts_batch(samples, bucket_name)
    
    elif len(args) >= 2:
        text, filename = args[0], args[1]
        bucket_name = kwargs.get('bucket_name', BUCKET_NAME)
        return create_and_upload_tts(text, filename, bucket_name)
    
    else:
        raise ValueError(
            "잘못된 인자입니다.\n"
            "단일 텍스트: create_and_upload_tts_flexible('텍스트', '파일명.mp3')\n"
            "여러 텍스트: create_and_upload_tts_flexible([('텍스트1', '파일1.mp3'), ('텍스트2', '파일2.mp3')])"
        )

        
if __name__ == "__main__":
    print("=== 단일 텍스트 처리 ===")
    single_result = create_and_upload_tts_flexible("안녕하세요, 반갑습니다.", "greeting.mp3", bucket_name=BUCKET_NAME)
    print(f"단일 결과: {single_result}")
    
    # 여러 텍스트 처리 예시
    print("\n=== 여러 텍스트 배치 처리 ===")
    samples = [
        ("진료 예약하고 싶어요.", "appointment_request.mp3"),
        ("처음 왔어요.", "first_visit.mp3"),
        # ("신분증 가져왔어요.", "id_card.mp3"),
        # ("오늘 예약 취소했어요.", "cancel_appointment.mp3"),
        # ("오늘 오전 예약 했어요.", "morning_appointment.mp3"),
        # ("오늘 오후 예약 했어요.", "afternoon_appointment.mp3"),
        # ("오늘 예약 변경했어요.", "change_appointment.mp3"),
        # ("오늘 예약 취소했어요.", "cancel_appointment.mp3"),
        # ("얼마나 걸려요?", "how_long.mp3"),
    ]
    
    batch_results = create_and_upload_tts_flexible(samples, bucket_name=BUCKET_NAME)
    
    print("\n=== 배치 처리 결과 ===")
    for text, filename, url in batch_results:
        status = "성공" if url else "실패"
        print(f"{filename}: {status} - {url}")
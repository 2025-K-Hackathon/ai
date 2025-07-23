import io
from google.cloud import storage
from google.cloud import texttospeech

BUCKET_NAME = 'dajeong-tts-audio'
KEY_PATH = './dj-tts-gcp-key.json'

storage_client = storage.Client.from_service_account_json(KEY_PATH)
tts_client = texttospeech.TextToSpeechClient.from_service_account_json(KEY_PATH)

# Google Cloud TTS로 오디오를 생성하여 바로 GCP Cloud Storage에 업로드
def create_and_upload_tts(text: str, filename: str, bucket_name: str) -> str | None:
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

        
if __name__ == "__main__":
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

    for text, filename in samples:
        print("=" * 30)
        print(f"변환할 텍스트: '{text}'")
        url = create_and_upload_tts(text=text, filename=filename, bucket_name=BUCKET_NAME)
        if url:
            print(f"-> 최종 결과물(URL): {url}")
        else:
            print("-> 생성 또는 업로드에 실패했거나, 파일이 이미 존재합니다.")
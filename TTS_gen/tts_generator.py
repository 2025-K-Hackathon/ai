import os
import io
from gtts import gTTS
from google.cloud import storage

BUCKET_NAME = 'dajeong-tts-audio'
KEY_PATH = './dj-tts-gcp-key.json'
storage_client = storage.Client.from_service_account_json(KEY_PATH)

# gTTS로 오디오를 생성하여 메모리에서 바로 GCP Cloud Storage에 업로드
def create_and_upload_tts(text: str, filename: str, bucket_name: str) -> str | None:
    try:
        # 이미 파일이 있는지 확인
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        
        if blob.exists():
            print(f"중복 파일: GCP 버킷 '{bucket_name}'에 '{filename}'이(가) 이미 존재합니다.")
            # 이미 존재하는 파일의 URL을 반환
            return blob.public_url
            # return None

        tts = gTTS(text=text, lang='ko')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        print(f"'{filename}'을(를) GCP 버킷 '{bucket_name}'에 업로드하는 중...")
        blob.upload_from_file(mp3_fp, content_type='audio/mpeg')
        
        public_url = blob.public_url
        print(f"업로드 성공! 공개 URL: {public_url}")
        
        return public_url
        
    except Exception as e:
        print(f"오디오 생성 또는 업로드 중 오류가 발생했습니다: {e}")
        return None

        
if __name__ == "__main__":
    samples = [
        # ("진료 예약하고 싶어요.", "appointment_request.mp3"),
        # ("처음 왔어요.", "first_visit.mp3"),
        # ("신분증 가져왔어요.", "id_card.mp3"),
        # ("오늘 예약 취소했어요.", "cancel_appointment.mp3"),
        # ("오늘 오전 예약 했어요.", "morning_appointment.mp3"),
        # ("오늘 오후 예약 했어요.", "afternoon_appointment.mp3"),
        # ("오늘 예약 변경했어요.", "change_appointment.mp3"),
        # ("오늘 예약 취소했어요.", "cancel_appointment.mp3"),
        # ("얼마나 걸려요?", "how_long.mp3"),
        ("안녕하세요. 현금 영수증 발행해주세요.", "cash_receipt.mp3"),
    ]

    for text, filename in samples:
        print("=" * 30)
        print(f"변환할 텍스트: '{text}'")
        url = create_and_upload_tts(text=text, filename=filename, bucket_name=BUCKET_NAME)
        if url:
            print(f"-> 최종 결과물(URL): {url}")
        else:
            print("-> 생성 또는 업로드에 실패했거나, 파일이 이미 존재합니다.")
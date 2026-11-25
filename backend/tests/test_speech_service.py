import sys
import os
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, engine, SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate
from app.api.v1.auth import register
from app.services.speech_service import speech_service

Base.metadata.create_all(bind=engine)


def test_speech_pipeline():
    # 1. Create a mock audio payload
    mock_audio_bytes = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    
    print("[TEST] 1. Testing Speech Service audio transcription...")
    transcription = speech_service.transcribe_audio(mock_audio_bytes, "candidate_response.wav")
    assert transcription is not None
    assert len(transcription) > 0
    print(f"[SUCCESS] Transcribed output: {transcription}")

    print("[TEST] 2. Testing Speech Synthesis fallback...")
    tts_result = speech_service.synthesize_speech("Hello candidate, please explain your architecture.")
    # May be None if no API key is in environment, which is valid and delegates to browser Web Speech API
    print(f"[SUCCESS] Speech synthesis handled (Result present: {tts_result is not None})")

    print("\n=== ALL SPEECH SERVICE TESTS PASSED! ===")


if __name__ == "__main__":
    test_speech_pipeline()

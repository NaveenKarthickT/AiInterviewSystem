import os
import io
import base64
import uuid
from typing import Optional
from app.core.config import settings


class SpeechService:
    """Service handling Speech-to-Text (STT) transcription and Text-to-Speech (TTS) synthesis.

    Priority order:
    1. OpenAI Whisper (if OPENAI_API_KEY set)
    2. Gemini audio understanding (if GEMINI_API_KEY set)
    3. Fallback marker string (no cloud key)
    """

    @staticmethod
    def transcribe_audio(file_bytes: bytes, filename: str) -> str:
        """Transcribe audio file bytes to text."""
        # 1. Try OpenAI Whisper
        if settings.OPENAI_API_KEY:
            try:
                import httpx
                headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
                files = {"file": (filename, file_bytes, "audio/webm")}
                data = {"model": "whisper-1"}
                response = httpx.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=30.0,
                )
                if response.status_code == 200:
                    return response.json().get("text", "").strip()
            except Exception as e:
                print(f"[WARN] OpenAI Whisper transcription failed: {e}. Trying Gemini STT.")

        # 2. Try Gemini audio understanding (via google-genai SDK)
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                from google.genai import types as genai_types

                client = genai.Client(api_key=settings.GEMINI_API_KEY)

                # Determine MIME type from filename
                ext = os.path.splitext(filename)[1].lower()
                mime_map = {
                    ".webm": "audio/webm",
                    ".mp3": "audio/mpeg",
                    ".wav": "audio/wav",
                    ".ogg": "audio/ogg",
                    ".m4a": "audio/mp4",
                    ".flac": "audio/flac",
                }
                mime_type = mime_map.get(ext, "audio/webm")

                # Encode audio as base64 inline part
                audio_part = genai_types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=mime_type,
                )

                response = client.models.generate_content(
                    model="gemini-2.0-flash-lite",
                    contents=[
                        genai_types.Content(
                            parts=[
                                genai_types.Part(text=(
                                    "You are a speech-to-text transcription engine. "
                                    "Transcribe ONLY what is spoken in this audio clip exactly as heard. "
                                    "Output ONLY the transcribed text with no explanations, no labels, no commentary."
                                )),
                                audio_part,
                            ]
                        )
                    ],
                )

                text = response.text.strip() if response.text else ""
                if text:
                    return text
            except Exception as e:
                print(f"[WARN] Gemini STT failed: {e}. No transcription available.")

        # 3. No cloud STT configured — return marker so frontend can show helpful message
        audio_size_kb = len(file_bytes) / 1024.0
        return f"[Audio Response Recorded: {round(audio_size_kb, 1)} KB received from {filename}]"

    @staticmethod
    def synthesize_speech(text: str, voice: str = "alloy") -> Optional[bytes]:
        """Synthesize text into spoken audio (MP3)."""
        if settings.OPENAI_API_KEY:
            try:
                import httpx
                headers = {
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                }
                payload = {"model": "tts-1", "input": text[:4000], "voice": voice}
                response = httpx.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers=headers,
                    json=payload,
                    timeout=30.0,
                )
                if response.status_code == 200:
                    return response.content
            except Exception as e:
                print(f"[WARN] OpenAI TTS synthesis failed: {e}.")

        return None


speech_service = SpeechService()


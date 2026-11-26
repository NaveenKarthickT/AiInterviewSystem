import os
import base64
from typing import Optional
from app.core.config import settings


class SpeechService:
    """Service handling Speech-to-Text (STT) transcription and Text-to-Speech (TTS) synthesis.

    Priority order for STT:
    1. OpenAI Whisper (if OPENAI_API_KEY set)
    2. Gemini audio understanding via REST (if GEMINI_API_KEY set)
    3. Fallback marker string (no cloud key configured)
    """

    @staticmethod
    def _get_mime_type(filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        mime_map = {
            ".webm": "audio/webm",
            ".mp3":  "audio/mpeg",
            ".wav":  "audio/wav",
            ".ogg":  "audio/ogg",
            ".m4a":  "audio/mp4",
            ".flac": "audio/flac",
            ".mp4":  "audio/mp4",
        }
        return mime_map.get(ext, "audio/webm")

    @staticmethod
    def transcribe_audio(file_bytes: bytes, filename: str) -> str:
        """Transcribe audio file bytes to text."""

        # ── 1. OpenAI Whisper ──────────────────────────────────────────────
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip():
            try:
                import httpx
                headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY.strip()}"}
                mime = SpeechService._get_mime_type(filename)
                files = {"file": (filename, file_bytes, mime)}
                data  = {"model": "whisper-1"}
                resp  = httpx.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers=headers, files=files, data=data, timeout=30.0,
                )
                if resp.status_code == 200:
                    text = resp.json().get("text", "").strip()
                    if text:
                        return text
            except Exception as e:
                print(f"[WARN] OpenAI Whisper failed: {e}. Trying Gemini STT.")

        # ── 2. Gemini audio understanding via REST API ─────────────────────
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
            try:
                import httpx

                api_key   = settings.GEMINI_API_KEY.strip()
                mime_type = SpeechService._get_mime_type(filename)
                audio_b64 = base64.b64encode(file_bytes).decode("utf-8")

                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"gemini-2.0-flash:generateContent?key={api_key}"
                )
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {
                                    "text": (
                                        "You are a speech-to-text transcription engine. "
                                        "Transcribe ONLY what is spoken in this audio clip exactly as heard. "
                                        "Output ONLY the transcribed text with no explanations, "
                                        "no labels, no commentary, no formatting."
                                    )
                                },
                                {
                                    "inline_data": {
                                        "mime_type": mime_type,
                                        "data": audio_b64,
                                    }
                                },
                            ]
                        }
                    ]
                }

                resp = httpx.post(url, json=payload, timeout=45.0)
                if resp.status_code == 200:
                    result = resp.json()
                    candidates = result.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        text  = " ".join(p.get("text", "") for p in parts).strip()
                        if text:
                            return text
                else:
                    print(f"[WARN] Gemini STT HTTP {resp.status_code}: {resp.text[:300]}")

            except Exception as e:
                print(f"[WARN] Gemini STT failed: {e}. No transcription available.")

        # ── 3. No cloud STT configured ─────────────────────────────────────
        audio_size_kb = len(file_bytes) / 1024.0
        return f"[Audio Response Recorded: {round(audio_size_kb, 1)} KB — please type your answer]"

    @staticmethod
    def synthesize_speech(text: str, voice: str = "alloy") -> Optional[bytes]:
        """Synthesize text into spoken audio (MP3)."""
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip():
            try:
                import httpx
                headers = {
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY.strip()}",
                    "Content-Type": "application/json",
                }
                payload  = {"model": "tts-1", "input": text[:4000], "voice": voice}
                response = httpx.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers=headers, json=payload, timeout=30.0,
                )
                if response.status_code == 200:
                    return response.content
            except Exception as e:
                print(f"[WARN] OpenAI TTS synthesis failed: {e}.")

        return None


speech_service = SpeechService()

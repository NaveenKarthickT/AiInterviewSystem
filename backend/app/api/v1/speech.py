import os
import uuid
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, status
from pydantic import BaseModel
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.speech_service import speech_service

router = APIRouter()

MAX_AUDIO_SIZE = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024  # bytes


class TranscriptionResponse(BaseModel):
    transcription: str
    filename: str
    file_size_bytes: int


class SynthesizeRequest(BaseModel):
    text: str
    voice: str = "alloy"


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload recorded candidate voice audio and return speech-to-text transcription."""
    allowed_exts = [".webm", ".wav", ".mp3", ".ogg", ".m4a"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_exts:
        # Default to webm if blob has no extension
        file_ext = ".webm"

    # Maximum audio size (bytes) – configurable via settings
    MAX_AUDIO_SIZE = settings.MAX_AUDIO_SIZE_MB * 1024 * 1024

    # Read uploaded file content
    content = await file.read()

    # Size cap check
    if len(content) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Audio file too large ({len(content)} bytes). Maximum allowed is {MAX_AUDIO_SIZE} bytes.",
        )
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded audio file is empty.",
        )

    # Save audio recording in uploads directory
    saved_filename = f"audio_{uuid.uuid4().hex}{file_ext}"
    saved_path = os.path.join(settings.UPLOAD_DIR, saved_filename)
    with open(saved_path, "wb") as f:
        f.write(content)

    transcribed_text = speech_service.transcribe_audio(content, file.filename or saved_filename)

    return TranscriptionResponse(
        transcription=transcribed_text,
        filename=saved_filename,
        file_size_bytes=len(content),
    )


@router.post("/synthesize")
def synthesize_speech_audio(
    req: SynthesizeRequest,
    current_user: User = Depends(get_current_user),
):
    """Synthesize question text into spoken interviewer audio."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    audio_bytes = speech_service.synthesize_speech(req.text, req.voice)
    if audio_bytes:
        return Response(content=audio_bytes, media_type="audio/mpeg")
    else:
        # If no cloud TTS key configured, return fallback status instructing client to use Web Speech API
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloud TTS not configured. Browser native Web Speech API will synthesize audio.",
        )

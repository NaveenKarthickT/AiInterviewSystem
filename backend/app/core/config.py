import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Adaptive Interview & Resume Optimization System"
    API_V1_STR: str = "api/v1"
    SECRET_KEY: str = "dev-secret-key-ai-adaptive-interview-system-2026-production-ready"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = "sqlite:///./interview_system.db"

    # LLM Settings
    DEFAULT_LLM_PROVIDER: str = "gemini"  # gemini, openai, groq, ollama
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    EXPORT_DIR: str = "./exports"

    # Security Limits
    MAX_UPLOAD_SIZE_MB: int = 10
    MAX_AUDIO_SIZE_MB: int = 25
    RATE_LIMIT_PER_MINUTE: int = 60

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"


settings = Settings()

# Ensure critical upload/export directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.EXPORT_DIR, exist_ok=True)

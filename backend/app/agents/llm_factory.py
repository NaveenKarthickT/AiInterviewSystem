import os
import json
from typing import Optional, Any
from app.core.config import settings


class LLMFactory:
    """Factory to initialize LLM clients based on configuration.
    
    Supports Google Gemini, OpenAI, Groq, and Ollama.
    """

    @staticmethod
    def get_llm(temperature: float = 0.2, model_name: Optional[str] = None):
        provider = settings.DEFAULT_LLM_PROVIDER.lower()

        # 1. Google Gemini
        if provider == "gemini" and settings.GEMINI_API_KEY:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                return ChatGoogleGenerativeAI(
                    model=model_name or "gemini-1.5-flash",
                    google_api_key=settings.GEMINI_API_KEY,
                    temperature=temperature,
                )
            except Exception as e:
                print(f"[WARN] Failed to initialize ChatGoogleGenerativeAI: {e}")

        # 2. OpenAI
        if provider == "openai" and settings.OPENAI_API_KEY:
            try:
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=model_name or "gpt-4o-mini",
                    api_key=settings.OPENAI_API_KEY,
                    temperature=temperature,
                )
            except Exception as e:
                print(f"[WARN] Failed to initialize ChatOpenAI: {e}")

        # Fallback / Direct Provider
        return None


llm_factory = LLMFactory()

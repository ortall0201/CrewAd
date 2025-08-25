# src/config.py
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Directories
    uploads_dir: str = "./uploads"
    outputs_dir: str = "./outputs"

    # Vector store (optional override)
    vector_store: Optional[str] = None

    # API keys (optional)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # TTS (optional)
    tts_engine: Optional[str] = None                # kokoro | openai | elevenlabs
    kokoro_lang: Optional[str] = "a"
    kokoro_voice: Optional[str] = "af_heart"
    kokoro_provider: Optional[str] = "local"        # local | deepinfra | fal
    kokoro_provider_url: Optional[str] = None
    kokoro_api_key: Optional[str] = None
    kokoro_fallback_provider: Optional[str] = "local"
    espeak_fallback_enabled: bool = True

    # Accept .env and IGNORE extras; map UPPERCASE env names automatically
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

def get_settings() -> Settings:
    s = Settings()
    # Ensure folders exist
    Path(s.uploads_dir).mkdir(parents=True, exist_ok=True)
    Path(s.outputs_dir).mkdir(parents=True, exist_ok=True)
    return s

settings = get_settings()

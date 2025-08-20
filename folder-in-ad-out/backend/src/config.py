import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # TTS settings
    tts_provider: str = "kokoro"  # kokoro, espeak, openai
    kokoro_model: str = "kokoro-v0_19"
    kokoro_lang: str = "a"
    kokoro_voice: str = "af_heart"
    openai_api_key: Optional[str] = None
    
    # Video settings
    video_fps: int = 30
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    
    # RAG settings
    rag_enabled: bool = True
    rag_model: str = "all-MiniLM-L6-v2"
    vector_store_path: str = "./backend/src/rag/index_db"
    
    # File paths
    base_dir: Path = Path(__file__).parent.parent.parent
    uploads_dir: Path = base_dir / "uploads"
    outputs_dir: Path = base_dir / "outputs"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def get_settings() -> Settings:
    return Settings()

settings = get_settings()

# Ensure directories exist
settings.uploads_dir.mkdir(exist_ok=True)
settings.outputs_dir.mkdir(exist_ok=True)

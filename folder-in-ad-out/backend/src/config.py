import os
from pydantic import BaseModel

class Settings(BaseModel):
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    output_dir: str = os.getenv("OUTPUT_DIR", "./outputs")

    tts_engine: str = os.getenv("TTS_ENGINE", "kokoro")
    kokoro_lang: str = os.getenv("KOKORO_LANG", "a")
    kokoro_voice: str = os.getenv("KOKORO_VOICE", "af_heart")
    kokoro_provider: str = os.getenv("KOKORO_PROVIDER", "local")
    kokoro_provider_url: str = os.getenv("KOKORO_PROVIDER_URL", "")

    vector_store_path: str = os.getenv("VECTOR_STORE", "./backend/src/rag/index_db")

settings = Settings()
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.output_dir, exist_ok=True)

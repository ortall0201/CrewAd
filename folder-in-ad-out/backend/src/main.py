import logging
import subprocess
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as api_router
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def configure_ffmpeg() -> str | None:
    """Configure FFmpeg for MoviePy and imageio."""
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        ffmpeg_exe = get_ffmpeg_exe()
        os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_exe

        # MoviePy config (works for 1.x and 2.x)
        import moviepy.config as mp_config  # type: ignore
        mp_config.FFMPEG_BINARY = ffmpeg_exe

        logger.info(f"✓ FFmpeg configured: {ffmpeg_exe}")
        return ffmpeg_exe
    except Exception as e:
        logger.warning(f"FFmpeg configuration failed: {e}. Video rendering may fail.")
        return None


def configure_imagemagick() -> bool:
    """Configure ImageMagick for MoviePy TextClip (kinetic text)."""
    try:
        imagemagick_binary = os.getenv("IMAGEMAGICK_BINARY", "magick")
        os.environ.setdefault("IMAGEMAGICK_BINARY", imagemagick_binary)

        try:
            subprocess.run([imagemagick_binary, "-version"], capture_output=True, check=True, timeout=10)

            # MoviePy hint (older versions read this global)
            import moviepy.config as mp_config  # type: ignore
            if hasattr(mp_config, "IMAGEMAGICK_BINARY"):
                mp_config.IMAGEMAGICK_BINARY = imagemagick_binary

            logger.info(f"✓ ImageMagick configured: {imagemagick_binary}")
            os.environ["ENABLE_KINETIC_TEXT"] = "true"
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning(f"ImageMagick not available at '{imagemagick_binary}'. TextClip features disabled.")
            os.environ["ENABLE_KINETIC_TEXT"] = "false"
            return False
    except Exception as e:
        logger.warning(f"ImageMagick configuration failed: {e}. TextClip features disabled.")
        os.environ["ENABLE_KINETIC_TEXT"] = "false"
        return False


def validate_dependencies() -> None:
    """Validate required system binaries on startup."""
    windows_paths = {
        "ffmpeg": [
            "ffmpeg",
            r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
        ],
        "espeak-ng": [
            "espeak-ng",
            r"C:\Program Files\eSpeak NG\espeak-ng.exe",
            r"C:\Program Files (x86)\eSpeak NG\espeak-ng.exe",
        ],
    }

    missing = []
    for name, candidates in windows_paths.items():
        version_flag = "-version" if name == "ffmpeg" else "--version"
        for path in candidates:
            try:
                subprocess.run([path, version_flag], capture_output=True, check=True)
                logger.info(f"✓ {name} is available at: {path}")
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        else:
            missing.append(name)
            logger.warning(f"✗ {name} not found in any of: {candidates}")

    if missing:
        logger.warning(f"Missing dependencies: {', '.join(missing)}")
        if "espeak-ng" in missing:
            logger.error("espeak-ng is required for voice synthesis (or use voice='mute').")
        if "ffmpeg" in missing:
            logger.warning("ffmpeg is required for video processing. Rendering may fail.")


def validate_python_packages() -> None:
    """Validate required Python packages (best-effort)."""
    # Core libs
    for package in ["moviepy", "chromadb"]:
        try:
            __import__(package)
            logger.info(f"✓ {package} package is available")
        except ImportError:
            logger.warning(f"✗ {package} package not found (some features will be disabled)")

    # Kokoro can be imported as 'kokoro' (newer) or 'kokoro_onnx' (0.4.x line)
    kokoro_ok = False
    for name in ("kokoro", "kokoro_onnx"):
        try:
            __import__(name)
            logger.info(f"✓ {name} package is available")
            kokoro_ok = True
            break
        except ImportError:
            continue
    if not kokoro_ok:
        logger.warning("✗ kokoro package not found (install `kokoro-onnx` or start with voice='mute').")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting folder-in-ad-out API...")

    configure_ffmpeg()
    configure_imagemagick()
    validate_dependencies()
    validate_python_packages()

    # Ensure directories exist (settings values may be str; wrap with Path)
    uploads_path = Path(settings.uploads_dir)
    outputs_path = Path(settings.outputs_dir)
    uploads_path.mkdir(parents=True, exist_ok=True)
    outputs_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Uploads directory: {uploads_path.resolve()}")
    logger.info(f"Outputs directory: {outputs_path.resolve()}")
    logger.info("API ready!")

    yield

    logger.info("Shutting down...")


app = FastAPI(
    title="Folder-in, Ad-out API",
    description="AI-native ad studio: Upload assets, generate ads",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS – adjust for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "uploads_dir": str(Path(settings.uploads_dir).resolve()),
        "outputs_dir": str(Path(settings.outputs_dir).resolve()),
    }


# API routes
app.include_router(api_router, prefix="/api")

import logging
import subprocess
import sys
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api.routes import router as api_router
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def configure_ffmpeg():
    """Configure FFmpeg for MoviePy and imageio"""
    try:
        # Use imageio_ffmpeg to get proper FFmpeg binary
        from imageio_ffmpeg import get_ffmpeg_exe
        ffmpeg_exe = get_ffmpeg_exe()
        os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_exe
        
        # Also configure MoviePy to use this FFmpeg
        from moviepy.config import change_settings
        change_settings({"FFMPEG_BINARY": ffmpeg_exe})
        
        logger.info(f"✓ FFmpeg configured: {ffmpeg_exe}")
        return ffmpeg_exe
    except Exception as e:
        logger.warning(f"FFmpeg configuration failed: {e}. Video rendering may fail.")
        return None

def configure_imagemagick():
    """Configure ImageMagick for MoviePy"""
    try:
        # Set ImageMagick binary path from env or default to 'magick'
        imagemagick_binary = os.getenv("IMAGEMAGICK_BINARY", "magick")
        os.environ.setdefault("IMAGEMAGICK_BINARY", imagemagick_binary)
        
        # Test if ImageMagick is available
        import subprocess
        try:
            subprocess.run([imagemagick_binary, "-version"], 
                         capture_output=True, check=True, timeout=10)
            
            # Configure MoviePy to use ImageMagick
            from moviepy.config import change_settings
            change_settings({"IMAGEMAGICK_BINARY": os.environ["IMAGEMAGICK_BINARY"]})
            
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

def validate_dependencies():
    """Validate required system dependencies on startup"""
    dependencies = {
        "ffmpeg": "ffmpeg",
        "espeak-ng": "espeak-ng"
    }
    
    # Try alternative paths for Windows installations
    windows_paths = {
        "ffmpeg": [
            "ffmpeg",
            r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
            r"C:\ProgramData\chocolatey\bin\ffmpeg",
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg"
        ],
        "espeak-ng": [
            "espeak-ng", 
            r"C:\Program Files\eSpeak NG\espeak-ng.exe",
            r"C:\Program Files (x86)\eSpeak NG\espeak-ng.exe"
        ]
    }
    
    missing = []
    for name, cmd in dependencies.items():
        found = False
        paths_to_try = windows_paths.get(name, [cmd])
        
        for path in paths_to_try:
            try:
                # Use appropriate version flag for each tool
                version_flag = "-version" if name == "ffmpeg" else "--version"
                subprocess.run([path, version_flag], capture_output=True, check=True)
                logger.info(f"✓ {name} is available at: {path}")
                found = True
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        if not found:
            missing.append(name)
            logger.warning(f"✗ {name} not found in any of: {paths_to_try}")
    
    if missing:
        logger.warning(f"Missing dependencies: {', '.join(missing)}")
        logger.warning("Some video features may not work properly. Install missing dependencies for full functionality")
        # Allow startup but warn about missing dependencies
        if "espeak-ng" in missing:
            logger.error("espeak-ng is required for voice synthesis. Please install it.")
        if "ffmpeg" in missing:
            logger.warning("ffmpeg is required for video processing. Video rendering may fail.")

def validate_python_packages():
    """Validate required Python packages"""
    required_packages = ["kokoro", "moviepy", "chromadb"]
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✓ {package} package is available")
        except ImportError:
            logger.warning(f"✗ {package} package not found (will use fallbacks)")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting folder-in-ad-out API...")
    configure_ffmpeg()
    configure_imagemagick()
    validate_dependencies()
    validate_python_packages()
    
    # Ensure directories exist
    settings.uploads_dir.mkdir(exist_ok=True)
    settings.outputs_dir.mkdir(exist_ok=True)
    
    logger.info(f"Uploads directory: {settings.uploads_dir}")
    logger.info(f"Outputs directory: {settings.outputs_dir}")
    logger.info("API ready!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(
    title="Folder-in, Ad-out API",
    description="AI-native ad studio: Upload assets, generate ads",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "uploads_dir": str(settings.uploads_dir),
        "outputs_dir": str(settings.outputs_dir)
    }

app.include_router(api_router, prefix="/api")

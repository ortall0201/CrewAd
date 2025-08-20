import logging
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api.routes import router as api_router
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_dependencies():
    """Validate required system dependencies on startup"""
    dependencies = {
        "ffmpeg": "ffmpeg",
        "espeak-ng": "espeak-ng"
    }
    
    missing = []
    for name, cmd in dependencies.items():
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            logger.info(f"✓ {name} is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(name)
            logger.warning(f"✗ {name} not found")
    
    if missing:
        logger.error(f"Missing dependencies: {', '.join(missing)}")
        logger.error("Please install ffmpeg and espeak-ng before running")
        sys.exit(1)

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
    allow_methods=["*"],
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

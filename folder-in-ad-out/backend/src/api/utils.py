import os
import json
import subprocess
import tempfile
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from ..config import settings

logger = logging.getLogger(__name__)

def validate_system_dependencies() -> Dict[str, bool]:
    """Check if required system dependencies are available"""
    dependencies = {}
    
    # Check ffmpeg
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            timeout=10
        )
        dependencies["ffmpeg"] = result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        dependencies["ffmpeg"] = False
    
    # Check espeak-ng
    try:
        result = subprocess.run(
            ["espeak-ng", "--version"], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL,
            timeout=10
        )
        dependencies["espeak"] = result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        dependencies["espeak"] = False
    
    return dependencies

def write_json(path: str, obj: Any) -> None:
    """Write object to JSON file with error handling"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)
        logger.debug(f"Wrote JSON to {path}")
    except Exception as e:
        logger.error(f"Failed to write JSON to {path}: {e}")
        raise

def read_json(path: str) -> Dict:
    """Read JSON file with error handling"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"JSON file not found: {path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Failed to read JSON from {path}: {e}")
        return {}

def safe_filename(name: str) -> str:
    """Create filesystem-safe filename"""
    # Remove or replace unsafe characters
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    cleaned = "".join(c if c in safe_chars else "_" for c in name)
    
    # Limit length and remove leading/trailing periods
    cleaned = cleaned[:255].strip(".")
    
    # Ensure not empty
    return cleaned if cleaned else "unnamed"

def get_file_info(file_path: str) -> Optional[Dict]:
    """Get file information including type detection"""
    if not os.path.exists(file_path):
        return None
    
    try:
        stat = os.stat(file_path)
        
        # Basic file info
        info = {
            "path": file_path,
            "name": os.path.basename(file_path),
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "is_file": os.path.isfile(file_path)
        }
        
        # Detect file type by extension
        ext = Path(file_path).suffix.lower()
        if ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp']:
            info["type"] = "image"
        elif ext in ['.wav', '.mp3', '.m4a', '.aac', '.ogg']:
            info["type"] = "audio"
        elif ext in ['.txt', '.md', '.json']:
            info["type"] = "text"
        else:
            info["type"] = "unknown"
        
        return info
        
    except Exception as e:
        logger.error(f"Failed to get file info for {file_path}: {e}")
        return None

def concat_audio_files(audio_files: List[str], output_path: str) -> bool:
    """Concatenate audio files using ffmpeg"""
    if not audio_files:
        logger.warning("No audio files to concatenate")
        return False
    
    if len(audio_files) == 1:
        # Single file, just copy
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", audio_files[0], 
                "-c", "copy", output_path
            ], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to copy single audio file: {e}")
            return False
    
    # Multiple files, concatenate
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            for audio_file in audio_files:
                # Use absolute path and escape for ffmpeg
                abs_path = os.path.abspath(audio_file)
                f.write(f"file '{abs_path}'\n")
            concat_file = f.name
        
        # Run ffmpeg concat
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
            "-i", concat_file, "-c", "copy", output_path
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Concatenated {len(audio_files)} audio files to {output_path}")
        
        # Clean up temp file
        os.unlink(concat_file)
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg concat failed: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Audio concatenation failed: {e}")
        return False

def cleanup_temp_files(directory: str, pattern: str = "temp_*") -> int:
    """Clean up temporary files in a directory"""
    if not os.path.exists(directory):
        return 0
    
    cleaned = 0
    try:
        for item in Path(directory).glob(pattern):
            if item.is_file():
                item.unlink()
                cleaned += 1
            elif item.is_dir():
                import shutil
                shutil.rmtree(item)
                cleaned += 1
        
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} temporary items from {directory}")
            
    except Exception as e:
        logger.error(f"Failed to cleanup temp files in {directory}: {e}")
    
    return cleaned

def estimate_video_duration(text_lines: List[str], wpm: int = 150) -> float:
    """Estimate video duration based on script word count and speaking rate"""
    if not text_lines:
        return 0.0
    
    total_words = sum(len(line.split()) for line in text_lines)
    duration_minutes = total_words / wpm
    duration_seconds = duration_minutes * 60
    
    # Add buffer time for pauses between lines
    buffer_time = len(text_lines) * 0.5
    
    return duration_seconds + buffer_time

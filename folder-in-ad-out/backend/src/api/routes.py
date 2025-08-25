import uuid
import os
import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    BackgroundTasks,
    Request,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ..config import settings
from ..crew.run_crew import run_pipeline, get_run_status, get_pipeline_stats

logger = logging.getLogger(__name__)
router = APIRouter()

# ----- Allowed types -----
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"}
ALLOWED_AUDIO_TYPES = {"audio/wav", "audio/mpeg", "audio/mp4", "audio/aac", "audio/ogg"}
ALLOWED_TEXT_TYPES = {"text/plain", "text/markdown", "application/json"}

# ----- Models -----
class RunRequest(BaseModel):
    run_id: str = Field(..., description="Run ID from the upload endpoint")
    target_length: int = Field(30, ge=5, le=120, description="Target video length in seconds")
    tone: str = Field("confident", description="Tone of voice for the ad")
    voice: str = Field("default", description="Voice to use (e.g. kokoro code, 'default', or 'mute')")
    aspect: str = Field("16:9", description="Video aspect ratio: 16:9 | 9:16 | 1:1")

    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "12345678-1234-5678-9012-123456789012",
                "target_length": 30,
                "tone": "confident",
                "voice": "default",
                "aspect": "16:9",
            }
        }

# ----- Upload -----
@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    run_id = str(uuid.uuid4())
    run_dir = Path(settings.uploads_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created upload directory: {run_dir}")

    saved_files = []
    file_info = []

    for file in files:
        if not file.filename:
            continue

        content_type = (file.content_type or "").lower()
        filename_lower = file.filename.lower()

        mime_type_allowed = (
            content_type in ALLOWED_IMAGE_TYPES
            or content_type in ALLOWED_AUDIO_TYPES
            or content_type in ALLOWED_TEXT_TYPES
        )
        extension_allowed = filename_lower.endswith(
            (
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
                ".gif",
                ".bmp",
                ".wav",
                ".mp3",
                ".m4a",
                ".aac",
                ".ogg",
                ".txt",
                ".md",
                ".json",
            )
        )

        if not (mime_type_allowed or extension_allowed):
            logger.warning(f"Skipping unsupported file: {file.filename} (type: {content_type})")
            continue

        try:
            data = await file.read()
            (run_dir / file.filename).write_bytes(data)
            saved_files.append(file.filename)
            file_info.append(
                {"filename": file.filename, "size": len(data), "type": content_type or "unknown", "saved": True}
            )
            logger.info(f"Saved file: {file.filename} ({len(data)} bytes)")
        except Exception as e:
            logger.error(f"Failed to save {file.filename}: {e}")
            file_info.append({"filename": file.filename, "saved": False, "error": str(e)})

    if not saved_files:
        raise HTTPException(status_code=400, detail="No valid files were uploaded")

    return {
        "run_id": run_id,
        "files": file_info,
        "total_files": len(saved_files),
        "upload_dir": str(run_dir),
    }

# ----- Helpers -----
def _normalize_aspect(value: str) -> str:
    v = (value or "").strip()
    # accept variants like "16x9", "1:1 ", etc.
    return v.replace("x", ":").replace(" ", "")

def _coerce_and_validate_payload(data: Dict[str, Any]) -> RunRequest:
    if "target_length" in data:
        try:
            data["target_length"] = int(data["target_length"])
        except Exception:
            pass

    if "aspect" in data and isinstance(data["aspect"], str):
        data["aspect"] = _normalize_aspect(data["aspect"])

    if not data.get("run_id"):
        raise HTTPException(status_code=422, detail="run_id is required")

    # pydantic validation (ranges etc.)
    payload = RunRequest(**data)

    valid_aspects = {"16:9", "9:16", "1:1"}
    if payload.aspect not in valid_aspects:
        raise HTTPException(status_code=400, detail="aspect must be '16:9', '9:16', or '1:1'")

    valid_tones = {"confident", "friendly", "professional", "casual", "urgent", "calm"}
    if payload.tone not in valid_tones:
        raise HTTPException(status_code=400, detail=f"tone must be one of: {', '.join(sorted(valid_tones))}")

    return payload

async def _validate_and_start_pipeline(
    background_tasks: BackgroundTasks,
    run_id: str,
    target_length: int,
    tone: str,
    voice: str,
    aspect: str,
):
    run_dir = Path(settings.uploads_dir) / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run ID {run_id} not found")

    logger.info(
        f"Starting pipeline for run {run_id}: length={target_length}s, tone={tone}, voice={voice}, aspect={aspect}"
    )

    background_tasks.add_task(run_pipeline_task, run_id, target_length, tone, voice, aspect)

    return {
        "run_id": run_id,
        "status": "started",
        "parameters": {
            "target_length": target_length,
            "tone": tone,
            "voice": voice,
            "aspect": aspect,
        },
    }

# ----- Run (accept JSON or form) -----
@router.post("/run")
async def start_pipeline(request: Request, background_tasks: BackgroundTasks):
    """
    Accepts application/json OR application/x-www-form-urlencoded.
    """
    data: Dict[str, Any] = {}

    # Try JSON first
    try:
        data = await request.json()
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}

    # If no JSON or empty, try form
    if not data:
        form = await request.form()
        data = dict(form)

    payload = _coerce_and_validate_payload(data)

    return await _validate_and_start_pipeline(
        background_tasks,
        payload.run_id,
        payload.target_length,
        payload.tone,
        payload.voice,
        payload.aspect,
    )

# Backward compatibility (explicit form endpoint)
@router.post("/run/form")
async def start_pipeline_form(
    background_tasks: BackgroundTasks,
    run_id: str = Form(...),
    target_length: int = Form(30),
    tone: str = Form("confident"),
    voice: str = Form("default"),
    aspect: str = Form("16:9"),
):
    payload = _coerce_and_validate_payload(
        {
            "run_id": run_id,
            "target_length": target_length,
            "tone": tone,
            "voice": voice,
            "aspect": aspect,
        }
    )
    return await _validate_and_start_pipeline(
        background_tasks,
        payload.run_id,
        payload.target_length,
        payload.tone,
        payload.voice,
        payload.aspect,
    )

# ----- Background task -----
async def run_pipeline_task(run_id: str, target_length: int, tone: str, voice: str, aspect: str):
    try:
        await run_pipeline(run_id, target_length, tone, voice, aspect)
    except Exception as e:
        logger.error(f"Pipeline task failed for {run_id}: {e}")

# ----- Status / Download / Admin -----
@router.get("/status/{run_id}")
async def get_status(run_id: str):
    status = get_run_status(run_id)
    if status.get("overall_status") == "not_found":
        raise HTTPException(status_code=404, detail=f"Run ID {run_id} not found")
    return status

@router.get("/download/{run_id}")
async def download_video(run_id: str):
    video_path = Path(settings.outputs_dir) / run_id / "ad_final.mp4"
    if not video_path.exists():
        status = get_run_status(run_id)
        if status.get("overall_status") == "not_found":
            raise HTTPException(status_code=404, detail=f"Run ID {run_id} not found")
        current = status.get("overall_status", "")
        if current in {"running", "started"}:
            raise HTTPException(status_code=202, detail="Video is still being processed")
        raise HTTPException(status_code=404, detail="Video not available")

    logger.info(f"Serving video download: {video_path} ({video_path.stat().st_size} bytes)")
    return FileResponse(path=str(video_path), media_type="video/mp4", filename=f"ad_{run_id}.mp4")

@router.get("/runs")
async def list_runs():
    return get_pipeline_stats()

@router.get("/run/{run_id}/files")
async def list_run_files(run_id: str):
    run_dir = Path(settings.uploads_dir) / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run ID {run_id} not found")

    files = []
    for p in run_dir.iterdir():
        if p.is_file():
            st = p.stat()
            files.append({"filename": p.name, "size": st.st_size, "modified": st.st_mtime})

    return {"run_id": run_id, "files": files, "total_files": len(files)}

@router.delete("/run/{run_id}")
async def delete_run(run_id: str):
    run_dir = Path(settings.uploads_dir) / run_id
    out_dir = Path(settings.outputs_dir) / run_id

    deleted_paths = []
    if run_dir.exists():
        import shutil

        shutil.rmtree(run_dir)
        deleted_paths.append(str(run_dir))
    if out_dir.exists():
        import shutil

        shutil.rmtree(out_dir)
        deleted_paths.append(str(out_dir))

    if not deleted_paths:
        raise HTTPException(status_code=404, detail=f"Run ID {run_id} not found")

    return {"run_id": run_id, "deleted": True, "paths_removed": deleted_paths}

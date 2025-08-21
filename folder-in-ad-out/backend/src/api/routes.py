import uuid
import os
import asyncio
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional, Union
from pydantic import BaseModel, Field
from ..config import settings
from ..crew.run_crew import run_pipeline, get_run_status, get_pipeline_stats

logger = logging.getLogger(__name__)
router = APIRouter()

# File type validation
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"}
ALLOWED_AUDIO_TYPES = {"audio/wav", "audio/mpeg", "audio/mp4", "audio/aac", "audio/ogg"}
ALLOWED_TEXT_TYPES = {"text/plain", "text/markdown", "application/json"}

# Request models
class RunRequest(BaseModel):
    """Request model for pipeline execution"""
    run_id: str = Field(..., description="Run ID from the upload endpoint")
    target_length: int = Field(30, ge=5, le=120, description="Target video length in seconds")
    tone: str = Field("confident", description="Tone of voice for the ad")
    voice: str = Field("default", description="Voice model to use for TTS")
    aspect: str = Field("16:9", description="Video aspect ratio")
    
    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "12345678-1234-5678-9012-123456789012",
                "target_length": 30,
                "tone": "confident",
                "voice": "default",
                "aspect": "16:9"
            }
        }

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload multiple files and return run_id for processing"""
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    run_id = str(uuid.uuid4())
    run_dir = os.path.join(settings.uploads_dir, run_id)
    os.makedirs(run_dir, exist_ok=True)
    
    logger.info(f"Created upload directory: {run_dir}")
    
    saved_files = []
    file_info = []
    
    for file in files:
        if not file.filename:
            continue
            
        # Validate file type - check both MIME type and extension
        content_type = file.content_type
        filename_lower = file.filename.lower()
        
        # Check by MIME type first
        mime_type_allowed = (
            content_type in ALLOWED_IMAGE_TYPES or 
            content_type in ALLOWED_AUDIO_TYPES or 
            content_type in ALLOWED_TEXT_TYPES
        )
        
        # Check by file extension as fallback
        extension_allowed = (
            # Images
            filename_lower.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp")) or
            # Audio
            filename_lower.endswith((".wav", ".mp3", ".m4a", ".aac", ".ogg")) or
            # Text/documents
            filename_lower.endswith((".txt", ".md", ".json"))
        )
        
        if not (mime_type_allowed or extension_allowed):
            logger.warning(f"Skipping unsupported file: {file.filename} (type: {content_type})")
            continue
        
        # Save file
        file_path = os.path.join(run_dir, file.filename)
        try:
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            saved_files.append(file_path)
            file_info.append({
                "filename": file.filename,
                "size": len(content),
                "type": content_type,
                "saved": True
            })
            
            logger.info(f"Saved file: {file.filename} ({len(content)} bytes)")
            
        except Exception as e:
            logger.error(f"Failed to save {file.filename}: {e}")
            file_info.append({
                "filename": file.filename,
                "saved": False,
                "error": str(e)
            })
    
    if not saved_files:
        raise HTTPException(status_code=400, detail="No valid files were uploaded")
    
    return {
        "run_id": run_id,
        "files": file_info,
        "total_files": len(saved_files),
        "upload_dir": run_dir
    }

async def _validate_and_start_pipeline(
    background_tasks: BackgroundTasks,
    run_id: str,
    target_length: int,
    tone: str,
    voice: str,
    aspect: str
):
    """Common validation and pipeline start logic"""
    # Validate run_id exists
    run_dir = os.path.join(settings.uploads_dir, run_id)
    if not os.path.exists(run_dir):
        raise HTTPException(status_code=404, detail=f"Run ID {run_id} not found")
    
    # Validate parameters
    if target_length < 5 or target_length > 120:
        raise HTTPException(status_code=400, detail="target_length must be between 5 and 120 seconds")
    
    if aspect not in ["16:9", "9:16", "1:1"]:
        raise HTTPException(status_code=400, detail="aspect must be '16:9', '9:16', or '1:1'")
    
    valid_tones = ["confident", "friendly", "professional", "casual", "urgent", "calm"]
    if tone not in valid_tones:
        raise HTTPException(status_code=400, detail=f"tone must be one of: {', '.join(valid_tones)}")
    
    logger.info(f"Starting pipeline for run {run_id}: length={target_length}s, tone={tone}, voice={voice}, aspect={aspect}")
    
    # Start pipeline in background
    background_tasks.add_task(
        run_pipeline_task,
        run_id, target_length, tone, voice, aspect
    )
    
    return {
        "run_id": run_id,
        "status": "started",
        "parameters": {
            "target_length": target_length,
            "tone": tone,
            "voice": voice,
            "aspect": aspect
        }
    }

@router.post("/run")
async def start_pipeline_json(
    request: RunRequest,
    background_tasks: BackgroundTasks
):
    """Start the ad creation pipeline with JSON body"""
    return await _validate_and_start_pipeline(
        background_tasks,
        request.run_id,
        request.target_length, 
        request.tone,
        request.voice,
        request.aspect
    )

@router.post("/run/form")
async def start_pipeline_form(
    background_tasks: BackgroundTasks,
    run_id: str = Form(...),
    target_length: int = Form(30),
    tone: str = Form("confident"),
    voice: str = Form("default"),
    aspect: str = Form("16:9"),
):
    """Start the ad creation pipeline with form data (legacy support)"""
    return await _validate_and_start_pipeline(
        background_tasks,
        run_id,
        target_length,
        tone,
        voice,
        aspect
    )

async def run_pipeline_task(run_id: str, target_length: int, tone: str, voice: str, aspect: str):
    """Background task to run the pipeline"""
    try:
        await run_pipeline(run_id, target_length, tone, voice, aspect)
    except Exception as e:
        logger.error(f"Pipeline task failed for {run_id}: {e}")

@router.get("/status/{run_id}")
async def get_status(run_id: str):
    """Get current pipeline status"""
    status = get_run_status(run_id)
    
    if status.get("overall_status") == "not_found":
        raise HTTPException(status_code=404, detail=f"Run ID {run_id} not found")
    
    return status

@router.get("/download/{run_id}")
async def download_video(run_id: str):
    """Download the final rendered video"""
    video_path = os.path.join(settings.outputs_dir, run_id, "ad_final.mp4")
    
    if not os.path.exists(video_path):
        # Check if run exists
        status = get_run_status(run_id)
        if status.get("overall_status") == "not_found":
            raise HTTPException(status_code=404, detail=f"Run ID {run_id} not found")
        
        # Check if pipeline is still running
        current_status = status.get("overall_status", "")
        if current_status in ["running", "started"]:
            raise HTTPException(status_code=202, detail="Video is still being processed")
        
        raise HTTPException(status_code=404, detail="Video not available")
    
    file_size = os.path.getsize(video_path)
    logger.info(f"Serving video download: {video_path} ({file_size} bytes)")
    
    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=f"ad_{run_id}.mp4"
    )

@router.get("/runs")
async def list_runs():
    """List all pipeline runs with their status"""
    return get_pipeline_stats()

@router.get("/run/{run_id}/files")
async def list_run_files(run_id: str):
    """List files associated with a run"""
    run_dir = os.path.join(settings.uploads_dir, run_id)
    if not os.path.exists(run_dir):
        raise HTTPException(status_code=404, detail=f"Run ID {run_id} not found")
    
    files = []
    for filename in os.listdir(run_dir):
        file_path = os.path.join(run_dir, filename)
        if os.path.isfile(file_path):
            stat = os.stat(file_path)
            files.append({
                "filename": filename,
                "size": stat.st_size,
                "modified": stat.st_mtime
            })
    
    return {
        "run_id": run_id,
        "files": files,
        "total_files": len(files)
    }

@router.delete("/run/{run_id}")
async def delete_run(run_id: str):
    """Delete a run and all associated files"""
    run_dir = os.path.join(settings.uploads_dir, run_id)
    output_dir = os.path.join(settings.outputs_dir, run_id)
    
    deleted_paths = []
    
    # Delete upload directory
    if os.path.exists(run_dir):
        import shutil
        shutil.rmtree(run_dir)
        deleted_paths.append(run_dir)
    
    # Delete output directory
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)
        deleted_paths.append(output_dir)
    
    if not deleted_paths:
        raise HTTPException(status_code=404, detail=f"Run ID {run_id} not found")
    
    return {
        "run_id": run_id,
        "deleted": True,
        "paths_removed": deleted_paths
    }

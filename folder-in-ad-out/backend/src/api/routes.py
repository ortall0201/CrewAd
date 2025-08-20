import uuid
import os
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional
from ..config import settings
from ..crew.run_crew import run_pipeline, get_run_status

router = APIRouter()

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    run_id = str(uuid.uuid4())
    run_dir = os.path.join(settings.upload_dir, run_id)
    os.makedirs(run_dir, exist_ok=True)

    saved = []
    for f in files:
        dest = os.path.join(run_dir, f.filename)
        with open(dest, "wb") as w:
            w.write(await f.read())
        saved.append(dest)

    return {"run_id": run_id, "files": [os.path.basename(p) for p in saved]}

@router.post("/run")
async def run(
    run_id: str = Form(...),
    target_length: int = Form(30),
    tone: str = Form("confident"),
    voice: str = Form("af_heart"),
    aspect: str = Form("16:9"),
):
    job = await run_pipeline(run_id, target_length, tone, voice, aspect)
    return {"run_id": run_id, "status": "started", "job": job}

@router.get("/status/{run_id}")
async def status(run_id: str):
    return get_run_status(run_id)

@router.get("/download/{run_id}")
def download(run_id: str):
    path = os.path.join(settings.output_dir, run_id, "ad_final.mp4")
    if not os.path.exists(path):
        return JSONResponse({"error": "Not ready"}, status_code=404)
    return FileResponse(path, media_type="video/mp4", filename=f"{run_id}.mp4")

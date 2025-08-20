import os, asyncio
from typing import Dict
from ..config import settings
from .tasks import task_curate, task_script, task_direct, task_tts, task_edit, task_qa

_RUNS: Dict[str, Dict] = {}  # in-memory status; replace with Redis in prod

def _set_status(run_id, step, status, extra=None):
    _RUNS.setdefault(run_id, {"steps": []})
    _RUNS[run_id]["steps"].append({"step": step, "status": status, "extra": extra})

def get_run_status(run_id: str):
    return _RUNS.get(run_id, {"steps": []})

async def run_pipeline(run_id: str, target_length: int, tone: str, voice: str, aspect: str):
    run_dir = os.path.join(settings.upload_dir, run_id)
    out_dir = os.path.join(settings.output_dir, run_id)
    os.makedirs(out_dir, exist_ok=True)

    try:
        _set_status(run_id, "curate", "start")
        assets = task_curate(run_dir)
        _set_status(run_id, "curate", "done", {"counts": {k: len(v) if isinstance(v, list) else int(bool(v)) for k,v in assets.items()}})

        _set_status(run_id, "script", "start")
        script = task_script(assets, target_length, tone)
        _set_status(run_id, "script", "done", {"chars": len(script)})

        _set_status(run_id, "direct", "start")
        shots = task_direct(script, assets)
        _set_status(run_id, "direct", "done", {"scenes": len(shots["scenes"])})

        _set_status(run_id, "tts", "start")
        wavs = task_tts(shots, voice=voice, lang=settings.kokoro_lang)
        _set_status(run_id, "tts", "done", {"wavs": len(wavs)})

        _set_status(run_id, "edit", "start")
        out_path = task_edit(run_id, shots, wavs, aspect)
        _set_status(run_id, "edit", "done", {"path": out_path})

        _set_status(run_id, "qa", "start")
        qa = task_qa(out_path)
        _set_status(run_id, "qa", "done", qa)

        _set_status(run_id, "complete", "done", {"success": qa.get("ok", False)})
        return {"ok": True}
    except Exception as e:
        _set_status(run_id, "error", "fail", {"error": str(e)})
        return {"ok": False, "error": str(e)}

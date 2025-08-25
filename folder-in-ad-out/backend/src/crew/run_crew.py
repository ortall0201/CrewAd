import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, List

from ..config import settings
from .agents import (
    AssetCuratorAgent,
    ScriptwrightAgent,
    DirectorAgent,
    NarratorAgent,
    MusicSupervisorAgent,
    EditorAgent,
    QAAgent,
)

logger = logging.getLogger(__name__)

# In-memory run registry (simple MVP state store)
_RUNS: Dict[str, Dict] = {}


def _init_run(run_id: str) -> None:
    _RUNS[run_id] = {
        "run_id": run_id,
        "overall_status": "started",
        "steps": [
            {"step": "curate", "status": "pending", "extra": None},
            {"step": "script", "status": "pending", "extra": None},
            {"step": "direct", "status": "pending", "extra": None},
            {"step": "narrate", "status": "pending", "extra": None},
            {"step": "music", "status": "pending", "extra": None},
            {"step": "edit", "status": "pending", "extra": None},
            {"step": "qa", "status": "pending", "extra": None},
        ],
    }


def _update_step(run_id: str, step: str, status: str, extra=None) -> None:
    run = _RUNS.get(run_id)
    if not run:
        return
    for s in run["steps"]:
        if s["step"] == step:
            s["status"] = status
            if extra is not None:
                s["extra"] = extra
            break


def _set_overall(run_id: str, status: str) -> None:
    if run_id in _RUNS:
        _RUNS[run_id]["overall_status"] = status


def get_run_status(run_id: str) -> Dict:
    return _RUNS.get(run_id, {"overall_status": "not_found", "run_id": run_id})


def get_pipeline_stats() -> Dict[str, Dict]:
    return _RUNS


# -----------------------------------------------------------------------------
# Main pipeline
# -----------------------------------------------------------------------------
async def run_pipeline(run_id: str, target_length: int, tone: str, voice: str, aspect: str) -> None:
    """
    Run the full pipeline. NOTE: No reference to settings.tts_provider anymore.
    The NarratorAgent decides (kokoro/espeak/silence) based on availability and 'voice'.
    """
    try:
        uploads_dir = Path(settings.uploads_dir) / run_id
        outputs_dir = Path(settings.outputs_dir) / run_id
        uploads_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting pipeline for run {run_id}")
        logger.info(f"Parameters: length={target_length}s, tone={tone}, voice={voice}, aspect={aspect}")
        logger.info(f"Run directory: {uploads_dir}")
        logger.info(f"Output directory: {outputs_dir}")

        # Initialize state
        _init_run(run_id)
        _set_overall(run_id, "running")

        # Instantiate agents
        curator = AssetCuratorAgent()
        writer = ScriptwrightAgent()
        director = DirectorAgent()
        narrator = NarratorAgent()
        music_sup = MusicSupervisorAgent()
        editor = EditorAgent()
        qa = QAAgent()

        # STEP 1: Curate
        _update_step(run_id, "curate", "running")
        assets = curator.curate(str(uploads_dir))
        _update_step(run_id, "curate", "completed", {"counts": {k: len(v) if isinstance(v, list) else (1 if v else 0) for k, v in assets.items()}})

        # STEP 2: Script
        _update_step(run_id, "script", "running")
        script_path = Path(uploads_dir) / "script.md"
        script_text = writer.draft(assets.get("brief") or "", target_length, tone, str(uploads_dir))
        _update_step(run_id, "script", "completed", {"chars": len(script_text), "lines": len([l for l in script_text.splitlines() if l.strip()])})

        # STEP 3: Director / Storyboard
        _update_step(run_id, "direct", "running")
        shots = director.storyboard(script_text, assets.get("images", []), str(uploads_dir))
        _update_step(run_id, "direct", "completed", {"scenes": len(shots.get("scenes", []))})

        # STEP 4: Narration (TTS)
        _update_step(run_id, "narrate", "running")
        # Decide language (used by kokoro/espeak). From env with safe defaults.
        lang = os.getenv("KOKORO_LANG", "a")  # kokoro language code, 'a' == en (American)
        # Lines to read:
        lines = [s["line"] for s in shots.get("scenes", [])]
        wavs = narrator.synth(lines, voice=voice, lang=lang, run_dir=str(uploads_dir))
        _update_step(run_id, "narrate", "completed", {"wavs": len(wavs)})

        # STEP 5: Music (stub)
        _update_step(run_id, "music", "running")
        bgm = music_sup.pick_and_duck(str(uploads_dir))
        _update_step(run_id, "music", "completed", {"bgm": bool(bgm)})

        # STEP 6: Edit / Render
        _update_step(run_id, "edit", "running")
        out_path = editor.render(run_id, shots, wavs, aspect, str(uploads_dir))
        _update_step(run_id, "edit", "completed", {"file": out_path})

        # STEP 7: QA
        _update_step(run_id, "qa", "running")
        qa_result = qa.audit(out_path, run_id, shots, str(uploads_dir))
        _update_step(run_id, "qa", "completed", qa_result)

        _set_overall(run_id, "success" if qa_result.get("status") == "ok" else "failed")
        logger.info("Pipeline complete for run %s: %s", run_id, _RUNS[run_id]["overall_status"])

    except Exception as e:
        logger.error("Pipeline failed for run %s: %s", run_id, e)
        _set_overall(run_id, "failed")
        # Try to attach a minimal error to the currently running step for UI
        try:
            for s in _RUNS.get(run_id, {}).get("steps", []):
                if s["status"] == "running":
                    s["status"] = "failed"
                    s["extra"] = {"error": str(e)}
                    break
        except Exception:
            pass

import os
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Any
from ..config import settings
from .tasks import (
    CurateTask, ScriptTask, DirectTask, NarrateTask,
    MusicTask, EditTask, QATask
)

logger = logging.getLogger(__name__)

# Thread-safe in-memory status storage (replace with Redis in production)
_runs_lock = threading.Lock()
_RUNS: Dict[str, Dict] = {}

def _set_status(run_id: str, step: str, status: str, extra: Any = None):
    """Thread-safe status update"""
    with _runs_lock:
        if run_id not in _RUNS:
            _RUNS[run_id] = {
                "run_id": run_id,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "steps": [],
                "current_step": step,
                "overall_status": status
            }
        
        step_info = {
            "step": step,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "extra": extra or {}
        }
        
        _RUNS[run_id]["steps"].append(step_info)
        _RUNS[run_id]["current_step"] = step
        _RUNS[run_id]["overall_status"] = status
        
        if status in ["done", "complete"]:
            _RUNS[run_id]["completed_at"] = datetime.now(timezone.utc).isoformat()

def get_run_status(run_id: str) -> Dict:
    """Get current pipeline status"""
    with _runs_lock:
        return _RUNS.get(run_id, {
            "run_id": run_id,
            "steps": [],
            "current_step": "not_found",
            "overall_status": "not_found"
        })

def list_all_runs() -> Dict:
    """Get all run statuses"""
    with _runs_lock:
        return dict(_RUNS)

class AdCreationPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self):
        self.tasks = {
            "curate": CurateTask(),
            "script": ScriptTask(),
            "direct": DirectTask(),
            "narrate": NarrateTask(),
            "music": MusicTask(),
            "edit": EditTask(),
            "qa": QATask()
        }
    
    async def run(self, run_id: str, target_length: int, tone: str, voice: str, aspect: str) -> Dict:
        """Execute the complete ad creation pipeline"""
        logger.info(f"Starting pipeline for run {run_id}")
        
        run_dir = os.path.join(settings.uploads_dir, run_id)
        output_dir = os.path.join(settings.outputs_dir, run_id)
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # 1. Asset Curation
            _set_status(run_id, "curate", "running")
            assets = self.tasks["curate"].execute(run_dir=run_dir)
            _set_status(run_id, "curate", "completed", {
                "image_count": len(assets.get("images", [])),
                "logo_count": len(assets.get("logos", [])),
                "audio_count": len(assets.get("audio", [])),
                "has_brief": bool(assets.get("brief"))
            })
            
            # 2. Script Generation
            _set_status(run_id, "script", "running")
            script = self.tasks["script"].execute(
                assets=assets,
                target_length=target_length,
                tone=tone,
                run_dir=run_dir
            )
            _set_status(run_id, "script", "completed", {
                "script_length": len(script),
                "word_count": len(script.split())
            })
            
            # 3. Storyboard Creation
            _set_status(run_id, "direct", "running")
            shots = self.tasks["direct"].execute(
                script=script,
                assets=assets,
                run_dir=run_dir
            )
            _set_status(run_id, "direct", "completed", {
                "scene_count": len(shots.get("scenes", []))
            })
            
            # 4. Voice Synthesis
            _set_status(run_id, "narrate", "running")
            wavs = self.tasks["narrate"].execute(
                shots=shots,
                voice=voice,
                lang=settings.kokoro_lang,
                run_dir=run_dir
            )
            _set_status(run_id, "narrate", "completed", {
                "audio_files": len(wavs),
                "tts_provider": settings.tts_provider
            })
            
            # 5. Music Supervision (MVP: skip)
            _set_status(run_id, "music", "running")
            music_path = self.tasks["music"].execute(run_dir=run_dir)
            _set_status(run_id, "music", "completed", {
                "has_music": bool(music_path)
            })
            
            # 6. Video Editing
            _set_status(run_id, "edit", "running")
            video_path = self.tasks["edit"].execute(
                run_id=run_id,
                shots=shots,
                wavs=wavs,
                aspect=aspect,
                run_dir=run_dir
            )
            _set_status(run_id, "edit", "completed", {
                "video_path": video_path,
                "file_exists": os.path.exists(video_path) if video_path else False
            })
            
            # 7. Quality Assurance
            _set_status(run_id, "qa", "running")
            qa_result = self.tasks["qa"].execute(
                video_path=video_path,
                run_id=run_id,
                shots=shots,
                run_dir=run_dir
            )
            _set_status(run_id, "qa", "completed", qa_result)
            
            # Pipeline complete
            success = qa_result.get("status") == "ok"
            _set_status(run_id, "complete", "success" if success else "failed", {
                "final_video": video_path,
                "success": success,
                "duration": qa_result.get("duration", 0)
            })
            
            logger.info(f"Pipeline completed for run {run_id}: {'success' if success else 'failed'}")
            return {
                "success": success,
                "run_id": run_id,
                "video_path": video_path,
                "metadata": qa_result
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed for run {run_id}: {e}")
            _set_status(run_id, "error", "failed", {
                "error": str(e),
                "error_type": type(e).__name__
            })
            return {
                "success": False,
                "run_id": run_id,
                "error": str(e)
            }

# Global pipeline instance
_pipeline = AdCreationPipeline()

async def run_pipeline(run_id: str, target_length: int, tone: str, voice: str, aspect: str) -> Dict:
    """Execute the ad creation pipeline"""
    return await _pipeline.run(run_id, target_length, tone, voice, aspect)

def get_pipeline_stats() -> Dict:
    """Get overall pipeline statistics"""
    with _runs_lock:
        total_runs = len(_RUNS)
        successful_runs = sum(1 for run in _RUNS.values() 
                             if run.get("overall_status") == "success")
        failed_runs = sum(1 for run in _RUNS.values() 
                         if run.get("overall_status") == "failed")
        running_runs = sum(1 for run in _RUNS.values() 
                          if run.get("overall_status") == "running")
        
        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "running_runs": running_runs,
            "success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0
        }

import os
import logging
import threading
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any
from pathlib import Path
from ..config import settings
from .tasks import (
    CurateTask, ScriptTask, DirectTask, NarrateTask,
    MusicTask, EditTask, QATask
)

logger = logging.getLogger(__name__)

def setup_run_logging(run_id: str) -> logging.Logger:
    """Set up per-run logging to individual log files"""
    output_dir = Path(settings.outputs_dir) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = output_dir / "pipeline.log"
    
    # Create run-specific logger
    run_logger = logging.getLogger(f"pipeline.{run_id}")
    run_logger.setLevel(logging.INFO)
    
    # Remove any existing handlers to avoid duplicates
    for handler in run_logger.handlers[:]:
        run_logger.removeHandler(handler)
    
    # Add file handler
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.INFO)
    
    # Add console handler  
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    run_logger.addHandler(file_handler)
    run_logger.addHandler(console_handler)
    
    # Prevent propagation to root logger to avoid double logging
    run_logger.propagate = False
    
    return run_logger

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
        
        run_dir = os.path.join(settings.uploads_dir, run_id)
        output_dir = os.path.join(settings.outputs_dir, run_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up run-specific logging AFTER creating output directory
        run_logger = setup_run_logging(run_id)
        run_logger.info(f"Starting pipeline for run {run_id}")
        run_logger.info(f"Parameters: length={target_length}s, tone={tone}, voice={voice}, aspect={aspect}")
        run_logger.info(f"Run directory: {run_dir}")
        run_logger.info(f"Output directory: {output_dir}")
        
        try:
            # 1. Asset Curation
            run_logger.info("=== STEP 1: Asset Curation ===")
            _set_status(run_id, "curate", "running")
            try:
                assets = await asyncio.to_thread(
                    self.tasks["curate"].execute,
                    run_dir=run_dir
                )
                run_logger.info(f"Asset curation completed: {len(assets.get('images', []))} images, {len(assets.get('logos', []))} logos, {len(assets.get('audio', []))} audio files")
                _set_status(run_id, "curate", "completed", {
                    "image_count": len(assets.get("images", [])),
                    "logo_count": len(assets.get("logos", [])),
                    "audio_count": len(assets.get("audio", [])),
                    "has_brief": bool(assets.get("brief"))
                })
            except Exception as e:
                run_logger.error(f"Asset curation failed: {e}")
                _set_status(run_id, "curate", "failed", {"error": str(e)})
                raise
            
            # 2. Script Generation
            run_logger.info("=== STEP 2: Script Generation ===")
            _set_status(run_id, "script", "running")
            try:
                script = await asyncio.to_thread(
                    self.tasks["script"].execute,
                    assets=assets,
                    target_length=target_length,
                    tone=tone,
                    run_dir=run_dir
                )
                run_logger.info(f"Script generation completed: {len(script)} characters, {len(script.split())} words")
                _set_status(run_id, "script", "completed", {
                    "script_length": len(script),
                    "word_count": len(script.split())
                })
            except Exception as e:
                run_logger.error(f"Script generation failed: {e}")
                _set_status(run_id, "script", "failed", {"error": str(e)})
                raise
            
            # 3. Storyboard Creation
            run_logger.info("=== STEP 3: Storyboard Creation ===")
            _set_status(run_id, "direct", "running")
            try:
                shots = await asyncio.to_thread(
                    self.tasks["direct"].execute,
                    script=script,
                    assets=assets,
                    run_dir=run_dir
                )
                run_logger.info(f"Storyboard creation completed: {len(shots.get('scenes', []))} scenes")
                _set_status(run_id, "direct", "completed", {
                    "scene_count": len(shots.get("scenes", []))
                })
            except Exception as e:
                run_logger.error(f"Storyboard creation failed: {e}")
                _set_status(run_id, "direct", "failed", {"error": str(e)})
                raise
            
            # 4. Voice Synthesis
            run_logger.info("=== STEP 4: Voice Synthesis ===")
            _set_status(run_id, "narrate", "running")
            try:
                wavs = await asyncio.to_thread(
                    self.tasks["narrate"].execute,
                    shots=shots,
                    voice=voice,
                    lang=settings.kokoro_lang,
                    run_dir=run_dir
                )
                run_logger.info(f"Voice synthesis completed: {len(wavs)} audio files generated")
                _set_status(run_id, "narrate", "completed", {
                    "audio_files": len(wavs),
                    "tts_provider": settings.tts_provider
                })
            except Exception as e:
                run_logger.error(f"Voice synthesis failed: {e}")
                _set_status(run_id, "narrate", "failed", {"error": str(e)})
                raise
            
            # 5. Music Supervision
            run_logger.info("=== STEP 5: Music Supervision ===")
            _set_status(run_id, "music", "running")
            try:
                music_path = await asyncio.to_thread(
                    self.tasks["music"].execute,
                    run_dir=run_dir
                )
                run_logger.info(f"Music supervision completed: {'music added' if music_path else 'no music'}")
                _set_status(run_id, "music", "completed", {
                    "has_music": bool(music_path)
                })
            except Exception as e:
                run_logger.error(f"Music supervision failed: {e}")
                _set_status(run_id, "music", "failed", {"error": str(e)})
                raise
            
            # 6. Video Editing
            run_logger.info("=== STEP 6: Video Editing ===")
            _set_status(run_id, "edit", "running")
            try:
                video_path = await asyncio.to_thread(
                    self.tasks["edit"].execute,
                    run_id=run_id,
                    shots=shots,
                    wavs=wavs,
                    aspect=aspect,
                    run_dir=run_dir
                )
                video_exists = os.path.exists(video_path) if video_path else False
                run_logger.info(f"Video editing completed: {video_path} ({'exists' if video_exists else 'missing'})")
                _set_status(run_id, "edit", "completed", {
                    "video_path": video_path,
                    "file_exists": video_exists
                })
            except Exception as e:
                run_logger.error(f"Video editing failed: {e}")
                _set_status(run_id, "edit", "failed", {"error": str(e)})
                raise
            
            # 7. Quality Assurance
            run_logger.info("=== STEP 7: Quality Assurance ===")
            _set_status(run_id, "qa", "running")
            try:
                qa_result = await asyncio.to_thread(
                    self.tasks["qa"].execute,
                    video_path=video_path,
                    run_id=run_id,
                    shots=shots,
                    run_dir=run_dir
                )
                run_logger.info(f"Quality assurance completed: status={qa_result.get('status', 'unknown')}")
                _set_status(run_id, "qa", "completed", qa_result)
            except Exception as e:
                run_logger.error(f"Quality assurance failed: {e}")
                _set_status(run_id, "qa", "failed", {"error": str(e)})
                raise
            
            # Pipeline complete
            success = qa_result.get("status") == "ok"
            run_logger.info("=== PIPELINE COMPLETE ===")
            run_logger.info(f"Final result: {'SUCCESS' if success else 'FAILED'}")
            run_logger.info(f"Video path: {video_path}")
            run_logger.info(f"Duration: {qa_result.get('duration', 0)}s")
            
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
            run_logger.error("=== PIPELINE FAILED ===")
            run_logger.error(f"Error: {e}")
            run_logger.error(f"Error type: {type(e).__name__}")
            
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
        finally:
            # Clean up logger handlers
            run_logger_name = f"pipeline.{run_id}"
            if run_logger_name in logging.Logger.manager.loggerDict:
                run_logger = logging.getLogger(run_logger_name)
                for handler in run_logger.handlers[:]:
                    handler.close()
                    run_logger.removeHandler(handler)

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

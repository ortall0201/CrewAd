import logging
import os
from typing import Dict, List, Any
from .agents import (
    AssetCuratorAgent, ScriptwrightAgent, DirectorAgent,
    NarratorAgent, MusicSupervisorAgent, EditorAgent, QAAgent
)

logger = logging.getLogger(__name__)

class PipelineTask:
    """Base class for pipeline tasks with logging and error handling"""
    
    def __init__(self, task_name: str):
        self.task_name = task_name
        
    def execute(self, **kwargs) -> Any:
        """Execute task with error handling and logging"""
        logger.info(f"Starting task: {self.task_name}")
        # Debug file for base execute method
        if self.task_name == "Video Rendering":
            debug_file = f"C:\\Users\\user\\Desktop\\CrewAd\\base-execute-debug.txt"
            with open(debug_file, "w") as f:
                f.write(f"BASE EXECUTE CALLED\n")
                f.write(f"Task: {self.task_name}\n")
                f.write(f"Kwargs: {kwargs}\n")
                f.write(f"About to call _run...\n")
        try:
            result = self._run(**kwargs)
            logger.info(f"Completed task: {self.task_name}")
            if self.task_name == "Video Rendering":
                with open(debug_file, "a") as f:
                    f.write(f"_run returned: {result}\n")
            return result
        except Exception as e:
            logger.error(f"Task {self.task_name} failed: {e}")
            if self.task_name == "Video Rendering":
                with open(debug_file, "a") as f:
                    f.write(f"_run failed with exception: {e}\n")
            raise
            
    def _run(self, **kwargs) -> Any:
        """Override in subclasses"""
        raise NotImplementedError

class CurateTask(PipelineTask):
    """Asset curation task"""
    
    def __init__(self):
        super().__init__("Asset Curation")
        
    def _run(self, run_dir: str) -> Dict:
        """Scan and categorize uploaded assets"""
        curator = AssetCuratorAgent()
        assets = curator.curate(run_dir)
        return assets

class ScriptTask(PipelineTask):
    """Script generation task"""
    
    def __init__(self):
        super().__init__("Script Generation")
        
    def _run(self, assets: Dict, target_length: int, tone: str, run_dir: str) -> str:
        """Generate script from brief and requirements"""
        scriptwright = ScriptwrightAgent()
        brief_path = assets.get("brief")
        script = scriptwright.draft(brief_path, target_length, tone, run_dir)
        return script

class DirectTask(PipelineTask):
    """Storyboard/directing task"""
    
    def __init__(self):
        super().__init__("Storyboard Creation")
        
    def _run(self, script: str, assets: Dict, run_dir: str) -> Dict:
        """Create visual storyboard from script and assets"""
        director = DirectorAgent()
        shots = director.storyboard(script, assets.get("images", []), run_dir)
        return shots

class NarrateTask(PipelineTask):
    """Text-to-speech task"""
    
    def __init__(self):
        super().__init__("Voice Synthesis")
        
    def _run(self, shots: Dict, voice: str, lang: str, run_dir: str) -> List[str]:
        """Generate TTS audio for each script line"""
        narrator = NarratorAgent()
        lines = [scene["line"] for scene in shots["scenes"]]
        wavs = narrator.synth(lines, voice, lang, run_dir)
        return wavs

class MusicTask(PipelineTask):
    """Music supervision task (MVP: stub)"""
    
    def __init__(self):
        super().__init__("Music Supervision")
        
    def _run(self, run_dir: str) -> str:
        """Select and process background music"""
        supervisor = MusicSupervisorAgent()
        music_path = supervisor.pick_and_duck(run_dir)
        return music_path or ""

class EditTask(PipelineTask):
    """Video editing/rendering task"""
    
    def __init__(self):
        super().__init__("Video Rendering")
        
    def _run(self, run_id: str, shots: Dict, wavs: List[str], aspect: str, run_dir: str) -> str:
        """Render final video with effects and audio"""
        # Write debug info to file for visibility
        debug_file = f"C:\\Users\\user\\Desktop\\CrewAd\\debug-{run_id}.txt"
        with open(debug_file, "w") as f:
            f.write(f"EDIT TASK STARTING\n")
            f.write(f"run_id: {run_id}\n")
            f.write(f"shots: {shots}\n")
            f.write(f"wavs: {wavs}\n")
            f.write(f"aspect: {aspect}\n")
            f.write(f"run_dir: {run_dir}\n")
            f.write(f"run_dir exists: {os.path.exists(run_dir) if run_dir else False}\n")
        
        print(f"🔥 EDIT TASK STARTING - run_id: {run_id}")
        print(f"🔥 Shots: {shots}")
        print(f"🔥 Wavs: {wavs}")
        print(f"🔥 Run dir: {run_dir}")
        logger.info("=== EDIT TASK STARTING ===")
        logger.info(f"EditTask inputs:")
        logger.info(f"  run_id: {run_id}")
        logger.info(f"  shots: {shots}")
        logger.info(f"  wavs: {wavs}")
        logger.info(f"  aspect: {aspect}")
        logger.info(f"  run_dir: {run_dir}")
        
        try:
            logger.info("Creating EditorAgent...")
            editor = EditorAgent()
            logger.info("Calling editor.render()...")
            video_path = editor.render(run_id, shots, wavs, aspect, run_dir)
            logger.info(f"EditorAgent returned: {video_path}")
            return video_path
        except Exception as e:
            logger.error(f"EditTask failed with exception: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # CRITICAL: Write exception details to file for debugging
            exception_file = f"C:\\Users\\user\\Desktop\\CrewAd\\edit-exception-{run_id}.txt"
            with open(exception_file, "w") as f:
                f.write(f"EDIT TASK EXCEPTION DETAILS\n")
                f.write(f"Exception: {e}\n")
                f.write(f"Exception type: {type(e).__name__}\n")
                f.write(f"Full traceback:\n{traceback.format_exc()}\n")
                f.write(f"Parameters:\n")
                f.write(f"  run_id: {run_id}\n")
                f.write(f"  shots: {shots}\n")
                f.write(f"  wavs: {wavs}\n")
                f.write(f"  aspect: {aspect}\n")
                f.write(f"  run_dir: {run_dir}\n")
            
            return ""

class QATask(PipelineTask):
    """Quality assurance task"""
    
    def __init__(self):
        super().__init__("Quality Assurance")
        
    def _run(self, video_path: str, run_id: str, shots: Dict, run_dir: str) -> Dict:
        """Validate output and generate metadata"""
        qa_agent = QAAgent()
        result = qa_agent.audit(video_path, run_id, shots, run_dir)
        return result

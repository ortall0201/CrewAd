import logging
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
        try:
            result = self._run(**kwargs)
            logger.info(f"Completed task: {self.task_name}")
            return result
        except Exception as e:
            logger.error(f"Task {self.task_name} failed: {e}")
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
        editor = EditorAgent()
        video_path = editor.render(run_id, shots, wavs, aspect, run_dir)
        return video_path

class QATask(PipelineTask):
    """Quality assurance task"""
    
    def __init__(self):
        super().__init__("Quality Assurance")
        
    def _run(self, video_path: str, run_id: str, shots: Dict, run_dir: str) -> Dict:
        """Validate output and generate metadata"""
        qa_agent = QAAgent()
        result = qa_agent.audit(video_path, run_id, shots, run_dir)
        return result

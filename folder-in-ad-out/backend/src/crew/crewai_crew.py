import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from crewai import Crew, Process
from .crewai_tasks import (
    create_asset_curation_task,
    create_script_generation_task,
    create_storyboard_task,
    create_narration_task,
    create_music_supervision_task,
    create_video_editing_task,
    create_qa_task
)
from ..config import settings

logger = logging.getLogger(__name__)

class CrewAIAdPipeline:
    """CrewAI-based ad creation pipeline"""
    
    def __init__(self):
        self.logger = logger
        
    def create_ad_crew(self, run_id: str, target_length: int, tone: str, voice: str, aspect: str, run_dir: str) -> Crew:
        """Create the CrewAI crew for ad generation"""
        
        # Create all tasks in sequence
        tasks = [
            create_asset_curation_task(run_dir),
            create_script_generation_task(run_dir, target_length, tone),
            create_storyboard_task(run_dir),
            create_narration_task(run_dir, voice),
            create_music_supervision_task(run_dir),
            create_video_editing_task(run_id, run_dir, aspect),
            create_qa_task(run_id, run_dir)
        ]
        
        # Create crew with sequential process
        crew = Crew(
            tasks=tasks,
            process=Process.sequential,  # Execute tasks in order
            verbose=2,  # Maximum verbosity for debugging
            memory=False,  # Disable memory for simpler execution
            max_execution_time=300,  # 5 minute timeout
            step_callback=self._step_callback
        )
        
        return crew
    
    def _step_callback(self, step_output):
        """Callback for tracking step progress"""
        logger.info(f"CrewAI Step completed: {step_output}")
    
    async def execute_pipeline(self, run_id: str, target_length: int, tone: str, voice: str, aspect: str) -> Dict[str, Any]:
        """Execute the complete CrewAI pipeline"""
        logger.info(f"Starting CrewAI pipeline for run {run_id}")
        
        # Set up directories
        run_dir = os.path.join(settings.uploads_dir, run_id)
        output_dir = os.path.join(settings.outputs_dir, run_id)
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Create the crew
            crew = self.create_ad_crew(run_id, target_length, tone, voice, aspect, run_dir)
            
            # Execute the crew with kickoff
            logger.info("🚀 Initiating CrewAI kickoff...")
            
            result = crew.kickoff(
                inputs={
                    "run_id": run_id,
                    "run_dir": run_dir,
                    "output_dir": output_dir,
                    "target_length": target_length,
                    "tone": tone,
                    "voice": voice,
                    "aspect": aspect
                }
            )
            
            logger.info("✅ CrewAI kickoff completed successfully")
            
            # Check for output video
            video_path = os.path.join(output_dir, "ad_final.mp4")
            success = os.path.exists(video_path)
            
            return {
                "success": success,
                "run_id": run_id,
                "video_path": video_path if success else "",
                "crew_result": str(result),
                "message": "CrewAI pipeline completed successfully" if success else "CrewAI pipeline completed but no video generated"
            }
            
        except Exception as e:
            logger.error(f"CrewAI pipeline failed for run {run_id}: {e}")
            return {
                "success": False,
                "run_id": run_id,
                "error": str(e),
                "message": "CrewAI pipeline execution failed"
            }

# Global CrewAI pipeline instance
crewai_pipeline = CrewAIAdPipeline()

async def run_crewai_pipeline(run_id: str, target_length: int, tone: str, voice: str, aspect: str) -> Dict[str, Any]:
    """Main entry point for CrewAI pipeline execution"""
    return await crewai_pipeline.execute_pipeline(run_id, target_length, tone, voice, aspect)
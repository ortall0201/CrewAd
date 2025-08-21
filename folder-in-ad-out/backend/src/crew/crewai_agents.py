import os
import json
import logging
from typing import Dict, List, Optional
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from ..config import settings

logger = logging.getLogger(__name__)

# Custom tools for file operations
class FileOperationTool(BaseTool):
    name: str = "file_operation"
    description: str = "Perform file operations like reading, writing, and listing files"

    def _run(self, operation: str, path: str, content: str = None) -> str:
        """Execute file operations"""
        try:
            if operation == "list":
                return str(os.listdir(path))
            elif operation == "read":
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif operation == "write" and content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"Written to {path}"
            elif operation == "exists":
                return str(os.path.exists(path))
        except Exception as e:
            return f"Error: {str(e)}"

class VideoOperationTool(BaseTool):
    name: str = "video_operation"
    description: str = "Perform video rendering operations using MoviePy"

    def _run(self, action: str, **kwargs) -> str:
        """Execute video operations"""
        try:
            if action == "render":
                from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
                
                # Basic video rendering logic
                run_id = kwargs.get('run_id', '')
                scenes = kwargs.get('scenes', [])
                
                # Create output directory
                output_dir = os.path.join(settings.outputs_dir, run_id)
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, "ad_final.mp4")
                
                # For now, create a simple test video
                from moviepy.editor import ColorClip
                test_clip = ColorClip(size=(1920, 1080), color=(0, 0, 255), duration=10)
                test_clip.write_videofile(output_path, fps=24, verbose=False, logger=None)
                
                return output_path
            return "Operation completed"
        except Exception as e:
            logger.error(f"Video operation failed: {e}")
            return f"Error: {str(e)}"

def create_asset_curator_agent():
    """Create the Asset Curator Agent using CrewAI"""
    return Agent(
        role="Asset Curator",
        goal="Analyze and categorize uploaded assets into a structured manifest",
        backstory="""You are an expert at organizing and categorizing digital assets. 
        You excel at identifying different types of media files and organizing them 
        for use in advertising campaigns.""",
        tools=[FileOperationTool()],
        verbose=True,
        allow_delegation=False
    )

def create_scriptwright_agent():
    """Create the Scriptwright Agent using CrewAI"""
    return Agent(
        role="Creative Scriptwriter",
        goal="Generate compelling ad copy from briefs and requirements",
        backstory="""You are a seasoned advertising copywriter with expertise in 
        creating persuasive, engaging scripts for video advertisements. You understand 
        how to match tone and messaging to target audiences.""",
        tools=[FileOperationTool()],
        verbose=True,
        allow_delegation=False
    )

def create_director_agent():
    """Create the Director Agent using CrewAI"""
    return Agent(
        role="Creative Director",
        goal="Map script lines to visual assets and create shot sequences",
        backstory="""You are a creative director with extensive experience in visual 
        storytelling. You excel at translating written scripts into compelling visual 
        sequences that engage audiences.""",
        tools=[FileOperationTool()],
        verbose=True,
        allow_delegation=False
    )

def create_narrator_agent():
    """Create the Narrator Agent using CrewAI"""
    return Agent(
        role="Voice Narrator",
        goal="Generate text-to-speech audio for script lines",
        backstory="""You are a professional voice artist and audio engineer who 
        specializes in creating high-quality text-to-speech audio for advertising 
        campaigns.""",
        tools=[FileOperationTool()],
        verbose=True,
        allow_delegation=False
    )

def create_music_supervisor_agent():
    """Create the Music Supervisor Agent using CrewAI"""
    return Agent(
        role="Music Supervisor",
        goal="Select and process background music for the advertisement",
        backstory="""You are a music supervisor with expertise in selecting 
        appropriate background music and audio ducking for video advertisements.""",
        tools=[FileOperationTool()],
        verbose=True,
        allow_delegation=False
    )

def create_editor_agent():
    """Create the Editor Agent using CrewAI"""
    return Agent(
        role="Video Editor",
        goal="Render the final video advertisement with all assets",
        backstory="""You are a professional video editor with expertise in using 
        MoviePy and other tools to create polished video advertisements with motion 
        effects, transitions, and audio synchronization.""",
        tools=[FileOperationTool(), VideoOperationTool()],
        verbose=True,
        allow_delegation=False
    )

def create_qa_agent():
    """Create the QA Agent using CrewAI"""
    return Agent(
        role="Quality Assurance Specialist",
        goal="Validate output quality and generate metadata for the final video",
        backstory="""You are a quality assurance specialist who ensures that video 
        advertisements meet technical and creative standards before delivery.""",
        tools=[FileOperationTool()],
        verbose=True,
        allow_delegation=False
    )
import os
import logging
from crewai import Task
from .crewai_agents import (
    create_asset_curator_agent,
    create_scriptwright_agent, 
    create_director_agent,
    create_narrator_agent,
    create_music_supervisor_agent,
    create_editor_agent,
    create_qa_agent
)

logger = logging.getLogger(__name__)

def create_asset_curation_task(run_dir: str):
    """Create task for asset curation"""
    return Task(
        description=f"""
        Analyze the files in the directory {run_dir} and create a structured manifest of all assets.
        
        Your task is to:
        1. List all files in the directory
        2. Categorize them into: images, logos, audio files, and text briefs
        3. Create an assets.json file with the categorized file paths
        4. Use absolute file paths in the manifest
        
        File categorization rules:
        - Images: .png, .jpg, .jpeg, .webp, .bmp, .gif files
        - Logos: image files with "logo" or "brand" in the filename
        - Audio: .wav, .mp3, .m4a, .aac, .ogg files  
        - Brief: .txt, .md, .json files with "brief", "style", "prompt", or "copy" in filename
        
        Expected output: Create and save assets.json file in the run directory.
        """,
        agent=create_asset_curator_agent(),
        expected_output="A JSON manifest file (assets.json) containing categorized asset paths"
    )

def create_script_generation_task(run_dir: str, target_length: int, tone: str):
    """Create task for script generation"""
    return Task(
        description=f"""
        Generate a compelling advertisement script based on the brief and requirements.
        
        Your task is to:
        1. Read the brief file from the assets.json manifest in {run_dir}
        2. Create an engaging script for a {target_length}-second advertisement
        3. Use a {tone} tone throughout the script
        4. Structure the script with clear line breaks for voice narration
        5. Save the script as script.md in the run directory
        
        Script requirements:
        - Target length: {target_length} seconds (approximately 2-3 words per second)
        - Tone: {tone}
        - Include a strong opening hook
        - Clear call-to-action at the end
        - Break into 3-5 distinct lines for visual scenes
        
        Expected output: A markdown script file saved as script.md
        """,
        agent=create_scriptwright_agent(),
        expected_output="A structured advertisement script saved as script.md file"
    )

def create_storyboard_task(run_dir: str):
    """Create task for storyboard/directing"""
    return Task(
        description=f"""
        Create a visual storyboard by mapping script lines to available images.
        
        Your task is to:
        1. Read the script.md file from {run_dir}
        2. Read the assets.json to see available images
        3. Map each script line to appropriate visual assets
        4. Create shot sequences with motion planning (Ken Burns effects)
        5. Save the storyboard as shots.json
        
        Storyboard structure:
        - Each scene should have: id, line (text), assets (image path), motion (zoom/pan direction)
        - Motion options: "zoom_in", "zoom_out", "pan_left", "pan_right", "static"
        - If insufficient images, reuse images with different motion
        - Each scene duration should be 3-6 seconds
        
        Expected output: A shots.json file with scene-by-scene visual planning
        """,
        agent=create_director_agent(),
        expected_output="A JSON storyboard file (shots.json) mapping script lines to visual assets"
    )

def create_narration_task(run_dir: str, voice: str = "default", lang: str = "en"):
    """Create task for text-to-speech narration"""
    return Task(
        description=f"""
        Generate text-to-speech audio files for each script line.
        
        Your task is to:
        1. Read the shots.json file from {run_dir}
        2. Extract the script lines from each scene
        3. Generate TTS audio for each line using voice: {voice}
        4. Save audio files in temp_audio/ subdirectory
        5. Use format: line_01_silent.wav, line_02_silent.wav, etc.
        
        Audio requirements:
        - Voice: {voice}
        - Language: {lang}
        - Format: WAV files
        - Clear speech at moderate pace
        - Consistent volume levels
        
        Expected output: Multiple WAV audio files in temp_audio/ directory
        """,
        agent=create_narrator_agent(),
        expected_output="WAV audio files for each script line in temp_audio/ directory"
    )

def create_music_supervision_task(run_dir: str):
    """Create task for music supervision"""
    return Task(
        description=f"""
        Handle background music selection and audio ducking for the advertisement.
        
        Your task is to:
        1. Check if any background music files are available in assets
        2. If available, prepare them for mixing with voice narration
        3. Implement audio ducking to reduce music volume during speech
        4. This is MVP implementation - can be a simple stub for now
        
        Expected output: Background music processing status (can be minimal for MVP)
        """,
        agent=create_music_supervisor_agent(),
        expected_output="Background music processing completed (MVP implementation)"
    )

def create_video_editing_task(run_id: str, run_dir: str, aspect: str):
    """Create task for video editing and rendering"""
    return Task(
        description=f"""
        Render the final video advertisement using MoviePy.
        
        Your task is to:
        1. Read shots.json for visual planning
        2. Read the generated audio files from temp_audio/
        3. Create video clips with Ken Burns motion effects
        4. Synchronize audio with visuals
        5. Render final video as ad_final.mp4
        6. Use aspect ratio: {aspect}
        
        Video specifications:
        - Resolution: 1920x1080 for 16:9, 1080x1920 for 9:16, 1080x1080 for 1:1
        - Frame rate: 30 fps
        - Format: MP4 with H.264 codec
        - Audio: AAC codec
        
        Output location: {run_id}/ad_final.mp4 in outputs directory
        
        Expected output: Rendered MP4 video file
        """,
        agent=create_editor_agent(),
        expected_output="Final rendered video file (ad_final.mp4) in outputs directory"
    )

def create_qa_task(run_id: str, run_dir: str):
    """Create task for quality assurance"""
    return Task(
        description=f"""
        Validate the final video output and generate quality metrics.
        
        Your task is to:
        1. Check if the final video file exists and is valid
        2. Measure video duration and file size
        3. Validate audio levels (LUFS measurement if possible)
        4. Generate metadata.json with video specifications
        5. Report overall quality status
        
        Quality checks:
        - Video file exists and is playable
        - Duration matches expected length
        - File size is reasonable (not corrupted)
        - Audio is present and audible
        
        Expected output: Quality validation report and metadata.json file
        """,
        agent=create_qa_agent(),
        expected_output="Quality assurance report and metadata.json file"
    )
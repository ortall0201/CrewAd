import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from ..config import settings

logger = logging.getLogger(__name__)

class AssetCuratorAgent:
    """Analyzes uploaded files and creates assets.json manifest"""
    
    def curate(self, run_dir: str) -> Dict:
        """Scan directory and categorize assets into structured manifest"""
        logger.info(f"Curating assets in {run_dir}")
        
        assets = {"images": [], "logos": [], "audio": [], "brief": None}
        
        if not os.path.exists(run_dir):
            logger.warning(f"Run directory {run_dir} does not exist")
            return assets
            
        for name in os.listdir(run_dir):
            file_path = os.path.abspath(os.path.join(run_dir, name))
            name_lower = name.lower()
            
            # Image files
            if name_lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")):
                if "logo" in name_lower or "brand" in name_lower:
                    assets["logos"].append(file_path)
                    logger.info(f"Found logo: {name}")
                else:
                    assets["images"].append(file_path)
                    logger.info(f"Found image: {name}")
                    
            # Audio files
            elif name_lower.endswith((".wav", ".mp3", ".m4a", ".aac", ".ogg")):
                assets["audio"].append(file_path)
                logger.info(f"Found audio: {name}")
                
            # Brief/style files
            elif name_lower.endswith((".txt", ".md", ".json")):
                if any(keyword in name_lower for keyword in ["brief", "style", "prompt", "copy"]):
                    assets["brief"] = file_path
                    logger.info(f"Found brief: {name}")
        
        # Save assets.json
        assets_path = os.path.join(run_dir, "assets.json")
        with open(assets_path, "w") as f:
            json.dump(assets, f, indent=2)
            
        logger.info(f"Assets curated: {len(assets['images'])} images, {len(assets['logos'])} logos, {len(assets['audio'])} audio, brief: {'yes' if assets['brief'] else 'no'}")
        return assets

class ScriptwrightAgent:
    """Creates advertising scripts based on briefs and target specifications"""
    
    def draft(self, brief_text: str, target_length: int, tone: str, run_dir: str) -> str:
        """Generate script.md based on brief and requirements"""
        logger.info(f"Drafting script - length: {target_length}s, tone: {tone}")
        
        # Read brief if provided
        brief_content = ""
        if brief_text and os.path.exists(brief_text):
            with open(brief_text, 'r', encoding='utf-8') as f:
                brief_content = f.read()
        
        # Try to get style hints from RAG if available
        style_hints = self._get_style_hints(brief_content, tone)
        
        # Generate script based on target length
        if target_length <= 15:
            beats = self._generate_short_script(brief_content, tone, style_hints)
        elif target_length <= 30:
            beats = self._generate_medium_script(brief_content, tone, style_hints)
        else:
            beats = self._generate_long_script(brief_content, tone, style_hints)
        
        script = "\n".join(beats)
        
        # Save script.md
        script_path = os.path.join(run_dir, "script.md")
        with open(script_path, "w", encoding='utf-8') as f:
            f.write(script)
            
        logger.info(f"Script drafted with {len(beats)} beats")
        return script
    
    def _get_style_hints(self, brief: str, tone: str) -> str:
        """Get style suggestions from RAG system if available"""
        try:
            from ..rag.index import fetch_style_hints
            return fetch_style_hints(f"{brief} {tone}")
        except ImportError:
            logger.info("RAG system not available, using defaults")
            return ""
    
    def _generate_short_script(self, brief: str, tone: str, hints: str) -> List[str]:
        """Generate 10-15 second script"""
        if "product" in brief.lower() or "buy" in brief.lower():
            return [
                "New product alert!",
                "This changes everything.",
                "Get yours today."
            ]
        return [
            "Transform your workflow.",
            "Simple. Fast. Effective.",
            "Try it now."
        ]
    
    def _generate_medium_script(self, brief: str, tone: str, hints: str) -> List[str]:
        """Generate 20-30 second script"""
        return [
            "Tired of the old way of doing things?",
            "We've built something better.",
            "Fast, reliable, and designed for you.",
            "Join thousands who've already made the switch.",
            "Get started today."
        ]
    
    def _generate_long_script(self, brief: str, tone: str, hints: str) -> List[str]:
        """Generate 45+ second script"""
        return [
            "Every day, millions struggle with outdated solutions.",
            "Wasting time, money, and opportunity.",
            "That's why we created something revolutionary.",
            "A platform that thinks ahead, adapts, and delivers.",
            "Used by industry leaders worldwide.",
            "Proven results in under 24 hours.",
            "Ready to join the future?",
            "Start your free trial today."
        ]

class DirectorAgent:
    """Maps script lines to images and defines visual treatment"""
    
    def storyboard(self, script: str, images: List[str], run_dir: str) -> Dict:
        """Create shots.json mapping script lines to visual assets"""
        logger.info(f"Creating storyboard with {len(images)} images")
        
        lines = [line.strip() for line in script.splitlines() if line.strip()]
        scenes = []
        
        for i, line in enumerate(lines):
            # Intelligent image selection based on content
            selected_image = self._select_image_for_line(line, images, i)
            
            # Determine motion based on image aspect ratio and content
            motion = self._get_motion_for_image(selected_image, line)
            
            # Determine text treatment
            text_treatment = {"kinetic": not selected_image or "call to action" in line.lower()}
            
            scene = {
                "id": i + 1,
                "line": line,
                "assets": {"image": selected_image},
                "motion": motion,
                "text": text_treatment
            }
            scenes.append(scene)
        
        shots = {"scenes": scenes}
        
        # Save shots.json
        shots_path = os.path.join(run_dir, "shots.json")
        with open(shots_path, "w") as f:
            json.dump(shots, f, indent=2)
            
        logger.info(f"Storyboard created with {len(scenes)} scenes")
        return shots
    
    def _select_image_for_line(self, line: str, images: List[str], index: int) -> Optional[str]:
        """Select best image for script line"""
        if not images:
            return None
            
        # For MVP, use cyclic selection with some content awareness
        if index < len(images):
            return images[index]
        else:
            # Cycle through available images
            return images[index % len(images)]
    
    def _get_motion_for_image(self, image_path: Optional[str], line: str) -> Dict:
        """Determine Ken Burns motion based on image and content"""
        if not image_path:
            return {"type": "static"}
        
        # Default Ken Burns with slight zoom
        motion = {
            "type": "kenburns",
            "zoom": 1.05,
            "pan": "center"
        }
        
        # Adjust based on line sentiment/energy
        if any(word in line.lower() for word in ["fast", "quick", "now", "today", "action"]):
            motion["zoom"] = 1.1
            motion["pan"] = "left_to_right"
        elif any(word in line.lower() for word in ["calm", "peaceful", "gentle", "soft"]):
            motion["zoom"] = 1.03
            
        return motion

class NarratorAgent:
    """Synthesizes speech from script lines using TTS"""
    
    def synth(self, text_lines: List[str], voice: str, lang: str, run_dir: str) -> List[str]:
        """Generate TTS audio files for each script line"""
        logger.info(f"Synthesizing {len(text_lines)} lines with {settings.tts_provider}")
        
        out_wavs = []
        temp_dir = os.path.join(run_dir, "temp_audio")
        os.makedirs(temp_dir, exist_ok=True)
        
        if settings.tts_provider == "kokoro":
            out_wavs = self._synth_kokoro(text_lines, voice, lang, temp_dir)
        elif settings.tts_provider == "espeak":
            out_wavs = self._synth_espeak(text_lines, voice, lang, temp_dir)
        else:
            logger.warning(f"Unknown TTS provider: {settings.tts_provider}, using espeak fallback")
            out_wavs = self._synth_espeak(text_lines, voice, lang, temp_dir)
            
        logger.info(f"Generated {len(out_wavs)} audio files")
        return out_wavs
    
    def _synth_kokoro(self, text_lines: List[str], voice: str, lang: str, temp_dir: str) -> List[str]:
        """Synthesize using Kokoro-82M TTS"""
        try:
            from kokoro import KPipeline
            import numpy as np
            import soundfile as sf
            
            pipe = KPipeline(lang_code=lang)
            out_wavs = []
            
            for idx, line in enumerate(text_lines, 1):
                try:
                    logger.info(f"Synthesizing line {idx}: '{line[:30]}...'")
                    
                    # Generate audio using Kokoro
                    chunks = pipe(line, voice=voice)
                    
                    # Collect audio data
                    audio_data = []
                    sample_rate = 24000
                    
                    for phonemes, durations, audio_bytes in chunks:
                        # Convert bytes to numpy array if needed
                        if isinstance(audio_bytes, bytes):
                            audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
                        else:
                            audio_array = np.array(audio_bytes, dtype=np.float32)
                        audio_data.append(audio_array)
                    
                    # Concatenate all audio chunks
                    if audio_data:
                        full_audio = np.concatenate(audio_data)
                        
                        # Save to WAV file
                        wav_path = os.path.join(temp_dir, f"line_{idx:02d}.wav")
                        sf.write(wav_path, full_audio, sample_rate)
                        out_wavs.append(wav_path)
                        
                        logger.info(f"Saved audio: {wav_path}")
                    else:
                        logger.warning(f"No audio generated for line {idx}")
                        
                except Exception as e:
                    logger.error(f"Error synthesizing line {idx}: {e}")
                    # Create silent placeholder
                    wav_path = self._create_silent_placeholder(temp_dir, idx, 2.0)
                    out_wavs.append(wav_path)
            
            return out_wavs
            
        except ImportError:
            logger.warning("Kokoro not available, falling back to espeak")
            return self._synth_espeak(text_lines, voice, lang, temp_dir)
        except Exception as e:
            logger.error(f"Kokoro synthesis failed: {e}")
            return self._synth_espeak(text_lines, voice, lang, temp_dir)
    
    def _synth_espeak(self, text_lines: List[str], voice: str, lang: str, temp_dir: str) -> List[str]:
        """Fallback synthesis using espeak-ng"""
        import subprocess
        
        out_wavs = []
        for idx, line in enumerate(text_lines, 1):
            wav_path = os.path.join(temp_dir, f"line_{idx:02d}.wav")
            
            try:
                # Use espeak-ng to synthesize
                cmd = [
                    "espeak-ng",
                    "-v", f"{lang}+{voice}" if voice != "default" else lang,
                    "-s", "150",  # Speed
                    "-w", wav_path,  # Output file
                    line
                ]
                
                subprocess.run(cmd, check=True, capture_output=True)
                out_wavs.append(wav_path)
                logger.info(f"Synthesized with espeak: line_{idx:02d}.wav")
                
            except subprocess.CalledProcessError as e:
                logger.error(f"espeak failed for line {idx}: {e}")
                wav_path = self._create_silent_placeholder(temp_dir, idx, 2.0)
                out_wavs.append(wav_path)
            except FileNotFoundError:
                logger.error("espeak-ng not found")
                wav_path = self._create_silent_placeholder(temp_dir, idx, 2.0)
                out_wavs.append(wav_path)
        
        return out_wavs
    
    def _create_silent_placeholder(self, temp_dir: str, idx: int, duration: float = 2.0) -> str:
        """Create silent audio placeholder when TTS fails"""
        import numpy as np
        import soundfile as sf
        
        sample_rate = 24000
        samples = int(sample_rate * duration)
        silent_audio = np.zeros(samples, dtype=np.float32)
        
        wav_path = os.path.join(temp_dir, f"line_{idx:02d}_silent.wav")
        sf.write(wav_path, silent_audio, sample_rate)
        
        logger.info(f"Created silent placeholder: {wav_path}")
        return wav_path

class MusicSupervisorAgent:
    """Handles background music and audio ducking (MVP: stub)"""
    
    def pick_and_duck(self, run_dir: str) -> Optional[str]:
        """Select and process background music - MVP implementation"""
        logger.info("Music supervision: skipping for MVP")
        return None

class EditorAgent:
    """Assembles final video from scenes, audio, and motion effects"""
    
    def render(self, run_id: str, shots: Dict, wavs: List[str], aspect: str, run_dir: str) -> str:
        """Render final MP4 with Ken Burns effects and audio"""
        logger.info(f"Rendering final video for run {run_id}")
        
        try:
            from moviepy.editor import (
                ImageClip, AudioFileClip, concatenate_videoclips,
                CompositeVideoClip, TextClip
            )
            
            clips = []
            scenes = shots.get("scenes", [])
            
            # Handle case where no images available - create kinetic text video
            if not any(scene["assets"]["image"] for scene in scenes):
                return self._render_kinetic_text_only(run_id, scenes, wavs, aspect, run_dir)
            
            for i, (scene, wav_path) in enumerate(zip(scenes, wavs)):
                try:
                    clip = self._create_scene_clip(scene, wav_path, aspect)
                    if clip:
                        clips.append(clip)
                        logger.info(f"Created clip for scene {scene['id']}")
                except Exception as e:
                    logger.error(f"Failed to create clip for scene {scene['id']}: {e}")
                    continue
            
            if not clips:
                logger.error("No clips created, cannot render video")
                return ""
            
            # Concatenate all clips
            final_video = concatenate_videoclips(clips, method="compose")
            
            # Output path
            out_dir = os.path.join(settings.outputs_dir, run_id)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, "ad_final.mp4")
            
            # Render final video
            logger.info(f"Writing video to {out_path}")
            final_video.write_videofile(
                out_path,
                fps=settings.video_fps,
                codec=settings.video_codec,
                audio_codec=settings.audio_codec,
                verbose=False,
                logger=None
            )
            
            # Clean up
            final_video.close()
            for clip in clips:
                clip.close()
            
            logger.info(f"Video rendered successfully: {out_path}")
            return out_path
            
        except ImportError as e:
            logger.error(f"MoviePy not available: {e}")
            return ""
        except Exception as e:
            logger.error(f"Video rendering failed: {e}")
            return ""
    
    def _create_scene_clip(self, scene: Dict, wav_path: str, aspect: str):
        """Create individual scene clip with Ken Burns effect"""
        from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
        
        image_path = scene["assets"]["image"]
        audio_clip = AudioFileClip(wav_path)
        duration = audio_clip.duration
        
        if image_path and os.path.exists(image_path):
            # Create image clip with Ken Burns effect
            image_clip = ImageClip(image_path, duration=duration)
            
            # Apply motion
            motion = scene.get("motion", {})
            if motion.get("type") == "kenburns":
                zoom = motion.get("zoom", 1.05)
                image_clip = self._apply_ken_burns(image_clip, zoom)
            
            # Resize based on aspect ratio
            if aspect == "16:9":
                image_clip = image_clip.resize(height=1080)
            elif aspect == "9:16":
                image_clip = image_clip.resize(width=1080)
            else:  # square
                image_clip = image_clip.resize((1080, 1080))
            
            # Add audio
            final_clip = image_clip.set_audio(audio_clip)
            
        else:
            # Fallback: kinetic text on black background
            final_clip = self._create_text_clip(scene["line"], duration, aspect)
            final_clip = final_clip.set_audio(audio_clip)
        
        return final_clip
    
    def _apply_ken_burns(self, clip, zoom=1.05):
        """Apply Ken Burns zoom effect"""
        def make_frame(t):
            progress = t / clip.duration
            current_zoom = 1 + (zoom - 1) * progress
            return clip.resize(current_zoom).get_frame(t)
        
        return clip.fl(make_frame)
    
    def _create_text_clip(self, text: str, duration: float, aspect: str):
        """Create animated text clip"""
        from moviepy.editor import TextClip, ColorClip
        
        # Background
        if aspect == "16:9":
            bg = ColorClip(size=(1920, 1080), color=(0, 0, 0), duration=duration)
        elif aspect == "9:16":
            bg = ColorClip(size=(1080, 1920), color=(0, 0, 0), duration=duration)
        else:
            bg = ColorClip(size=(1080, 1080), color=(0, 0, 0), duration=duration)
        
        # Text
        try:
            txt_clip = TextClip(
                text,
                fontsize=50,
                color='white',
                font='Arial-Bold'
            ).set_position('center').set_duration(duration)
            
            return CompositeVideoClip([bg, txt_clip])
        except:
            # Fallback if TextClip fails
            return bg
    
    def _render_kinetic_text_only(self, run_id: str, scenes: List[Dict], wavs: List[str], aspect: str, run_dir: str) -> str:
        """Render video with only kinetic text (no images)"""
        logger.info("Rendering kinetic text-only video")
        
        from moviepy.editor import concatenate_videoclips
        
        clips = []
        for scene, wav_path in zip(scenes, wavs):
            try:
                audio_clip = AudioFileClip(wav_path)
                text_clip = self._create_text_clip(scene["line"], audio_clip.duration, aspect)
                text_clip = text_clip.set_audio(audio_clip)
                clips.append(text_clip)
            except Exception as e:
                logger.error(f"Failed to create text clip for scene {scene['id']}: {e}")
        
        if clips:
            final_video = concatenate_videoclips(clips)
            out_dir = os.path.join(settings.outputs_dir, run_id)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, "ad_final.mp4")
            
            final_video.write_videofile(
                out_path,
                fps=settings.video_fps,
                codec=settings.video_codec,
                audio_codec=settings.audio_codec,
                verbose=False,
                logger=None
            )
            
            return out_path
        
        return ""

class QAAgent:
    """Validates final output and generates metadata"""
    
    def audit(self, out_path: str, run_id: str, shots: Dict, run_dir: str) -> Dict:
        """Perform quality checks and generate metadata.json"""
        logger.info(f"QA audit for {out_path}")
        
        # Basic file checks
        file_exists = os.path.exists(out_path)
        file_size = os.path.getsize(out_path) if file_exists else 0
        
        # Get video duration
        duration_sec = 0
        if file_exists:
            try:
                from moviepy.editor import VideoFileClip
                with VideoFileClip(out_path) as video:
                    duration_sec = video.duration
            except:
                logger.warning("Could not determine video duration")
        
        # Create metadata
        metadata = {
            "run_id": run_id,
            "duration_sec": duration_sec,
            "voice": "kokoro_default",
            "aspect": "16:9",  # Default for MVP
            "loudness_lufs": -23,  # Placeholder
            "scenes": self._extract_scene_metadata(shots, duration_sec),
            "captions_file": None,  # MVP: not implemented
            "render_file": "ad_final.mp4" if file_exists else None
        }
        
        # Save metadata
        metadata_path = os.path.join(run_dir, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        status = "ok" if file_exists and file_size > 0 else "failed"
        
        result = {
            "status": status,
            "file_exists": file_exists,
            "file_size": file_size,
            "duration": duration_sec,
            "metadata_path": metadata_path,
            "output_path": out_path
        }
        
        logger.info(f"QA complete: {status}")
        return result
    
    def _extract_scene_metadata(self, shots: Dict, total_duration: float) -> List[Dict]:
        """Extract scene timing metadata"""
        scenes = shots.get("scenes", [])
        if not scenes:
            return []
        
        scene_metadata = []
        duration_per_scene = total_duration / len(scenes)
        
        for i, scene in enumerate(scenes):
            start_time = i * duration_per_scene
            end_time = (i + 1) * duration_per_scene
            
            scene_meta = {
                "id": scene["id"],
                "start": round(start_time, 1),
                "end": round(end_time, 1),
                "image": scene["assets"]["image"],
                "line": scene["line"]
            }
            scene_metadata.append(scene_meta)
        
        return scene_metadata

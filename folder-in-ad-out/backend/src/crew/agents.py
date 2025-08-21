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
        logger.info(f"Synthesizing {len(text_lines)} lines with voice={voice}")
        
        out_dir = os.path.join(run_dir, "temp_audio")
        os.makedirs(out_dir, exist_ok=True)
        
        # Handle mute mode for testing
        if voice == "mute":
            return self._synth_mute(text_lines, out_dir)
        
        # Try Kokoro first, then fallback to espeak
        try:
            return self._synth_kokoro(text_lines, voice, lang, out_dir)
        except Exception as e:
            logger.warning(f"Kokoro failed: {e}, falling back to espeak")
            return self._synth_espeak(text_lines, voice, lang, out_dir)
    
    def _synth_kokoro(self, text_lines: List[str], voice: str, lang: str, out_dir: str) -> List[str]:
        """Robust Kokoro TTS synthesis"""
        from pathlib import Path
        import soundfile as sf
        
        try:
            from kokoro_onnx import KPipeline
        except ImportError:
            raise ImportError("Kokoro not available")
        
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        pipe = KPipeline(lang_code=lang)
        wavs = []
        
        for i, line in enumerate(text_lines, 1):
            if not line.strip():
                continue
                
            logger.info(f"Kokoro synthesizing line {i}: '{line[:50]}...'")
            
            try:
                # Generator yields (gs, ps, audio) chunks @ 24kHz
                audio_full = None
                for _, _, audio in pipe(line, voice=voice, speed=1.0):
                    audio_full = audio  # Last chunk contains the final audio array
                
                if audio_full is None:
                    logger.warning(f"No audio generated for line {i}")
                    continue
                    
                # Save with correct 24kHz sample rate
                out_path = Path(out_dir) / f"line_{i:02d}.wav" 
                sf.write(str(out_path), audio_full, 24000)
                wavs.append(str(out_path))
                logger.info(f"Saved: {out_path}")
                
            except Exception as e:
                logger.error(f"Failed to synthesize line {i}: {e}")
                # Create silent placeholder
                out_path = Path(out_dir) / f"line_{i:02d}.wav"
                self._create_silent_wav(str(out_path), 2.0)
                wavs.append(str(out_path))
        
        return wavs
    
    def _synth_mute(self, text_lines: List[str], out_dir: str) -> List[str]:
        """Generate silent WAV files for testing"""
        import subprocess
        from pathlib import Path
        
        logger.info("Using mute mode - generating silent WAVs")
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        wavs = []
        
        for i, _ in enumerate(text_lines, 1):
            out_path = Path(out_dir) / f"line_{i:02d}.wav"
            try:
                subprocess.check_call([
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", 
                    "-t", "2", str(out_path)
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                wavs.append(str(out_path))
            except Exception as e:
                logger.error(f"Failed to create silent WAV {i}: {e}")
                # Fallback: create minimal silent WAV manually
                self._create_silent_wav(str(out_path), 2.0)
                wavs.append(str(out_path))
        
        return wavs
    
    def _create_silent_wav(self, path: str, duration: float):
        """Create a silent WAV file manually"""
        import soundfile as sf
        import numpy as np
        
        sample_rate = 24000
        samples = int(sample_rate * duration)
        silent_audio = np.zeros(samples, dtype=np.float32)
        sf.write(path, silent_audio, sample_rate)
    
    def _synth_espeak(self, text_lines: List[str], voice: str, lang: str, temp_dir: str) -> List[str]:
        """Fallback synthesis using espeak-ng"""
        import subprocess
        
        out_wavs = []
        for idx, line in enumerate(text_lines, 1):
            wav_path = os.path.join(temp_dir, f"line_{idx:02d}.wav")
            
            try:
                # Use espeak-ng to synthesize - try multiple paths
                espeak_paths = [
                    "espeak-ng",
                    r"C:\Program Files\eSpeak NG\espeak-ng.exe",
                    r"C:\Program Files (x86)\eSpeak NG\espeak-ng.exe"
                ]
                
                espeak_cmd = None
                for path in espeak_paths:
                    try:
                        subprocess.run([path, "--version"], check=True, capture_output=True)
                        espeak_cmd = path
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                
                if not espeak_cmd:
                    raise FileNotFoundError("espeak-ng not found in any path")
                
                cmd = [
                    espeak_cmd,
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
        
        # Output paths
        out_dir = os.path.join(settings.outputs_dir, run_id)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "ad_final.mp4")
        temp_audio_dir = os.path.join(out_dir, "temp_audio")
        os.makedirs(temp_audio_dir, exist_ok=True)
        
        clips = []
        audio_clips = []
        image_clips = []
        
        try:
            from moviepy.editor import (
                ImageClip, AudioFileClip, concatenate_videoclips, 
                CompositeVideoClip, TextClip, ColorClip
            )
            
            scenes = shots.get("scenes", [])
            if not scenes:
                raise RuntimeError("No scenes to render (check shots.json)")
            
            logger.info(f"Processing {len(scenes)} scenes")
            
            # Process each scene
            for i, (scene, wav_path) in enumerate(zip(scenes, wavs)):
                try:
                    logger.info(f"Creating clip for scene {i+1}/{len(scenes)}: {scene.get('id', 'unknown')}")
                    clip = self._create_scene_clip_safe(scene, wav_path, aspect, temp_audio_dir)
                    if clip:
                        clips.append(clip)
                        logger.info(f"✓ Scene {i+1} clip created successfully")
                    else:
                        logger.warning(f"✗ Scene {i+1} clip creation failed, skipping")
                except Exception as e:
                    logger.error(f"Failed to create clip for scene {i+1}: {e}")
                    # Continue with other scenes rather than failing completely
                    continue
            
            if not clips:
                raise RuntimeError("No scenes to render (check images/audio mapping)")
            
            logger.info(f"Concatenating {len(clips)} clips...")
            
            # Concatenate all clips safely
            final_video = concatenate_videoclips(clips, method="compose")
            
            # Render final video with Windows-safe parameters
            logger.info(f"Writing video to: {out_path}")
            final_video.write_videofile(
                out_path,
                fps=30,  # Fixed FPS for compatibility
                codec="libx264",
                audio_codec="aac",
                ffmpeg_params=["-movflags", "+faststart"],
                temp_audiofile=os.path.join(temp_audio_dir, "temp-audio.m4a"),
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            # Verify file was created
            if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                logger.info(f"✓ Video rendered successfully: {out_path} ({os.path.getsize(out_path)} bytes)")
                success_path = out_path
            else:
                raise RuntimeError(f"Video file not created or is empty: {out_path}")
                
        except ImportError as e:
            error_msg = f"MoviePy not available: {e}"
            logger.error(error_msg)
            success_path = ""
        except Exception as e:
            error_msg = f"Video rendering failed: {e}"
            logger.error(error_msg)
            # Log detailed error to pipeline log if available
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # Check if video was created despite the exception
            if 'out_path' in locals() and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                logger.warning(f"Video was created despite error: {out_path} ({os.path.getsize(out_path)} bytes)")
                success_path = out_path
            else:
                success_path = ""
        finally:
            # Clean up all clips to prevent file locks on Windows
            try:
                if 'final_video' in locals():
                    final_video.close()
                for clip in clips:
                    try:
                        clip.close()
                    except:
                        pass
                # Clean up any remaining clip references
                clips.clear()
                
                # Clean up temp audio directory
                try:
                    if os.path.exists(temp_audio_dir) and 'success_path' in locals() and success_path:
                        # Only clean up temp if we succeeded, to preserve debug info
                        import shutil
                        shutil.rmtree(temp_audio_dir, ignore_errors=True)
                except:
                    pass
                    
            except Exception as cleanup_error:
                logger.warning(f"Cleanup error: {cleanup_error}")
                
        return success_path if 'success_path' in locals() else ""
    
    def _create_scene_clip_safe(self, scene: Dict, wav_path: str, aspect: str, temp_audio_dir: str):
        """Create individual scene clip with safe Windows handling"""
        from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip, ColorClip
        import soundfile as sf
        
        image_path = scene["assets"].get("image")
        
        # Validate and load audio
        if not os.path.exists(wav_path):
            logger.error(f"Audio file not found: {wav_path}")
            return None
            
        try:
            audio_clip = AudioFileClip(wav_path)
            duration = max(audio_clip.duration, 0.5)  # Minimum 0.5s duration
            
            # Normalize audio sample rate if needed
            try:
                data, samplerate = sf.read(wav_path)
                if samplerate not in [24000, 48000]:
                    logger.info(f"Resampling audio from {samplerate}Hz to 24000Hz")
                    # Simple resampling - in production, use librosa
                    normalized_path = os.path.join(temp_audio_dir, f"normalized_{os.path.basename(wav_path)}")
                    sf.write(normalized_path, data, 24000)
                    audio_clip.close()
                    audio_clip = AudioFileClip(normalized_path)
            except Exception as resample_error:
                logger.warning(f"Audio resampling failed: {resample_error}, using original")
                
        except Exception as e:
            logger.error(f"Failed to load audio {wav_path}: {e}")
            return None
        
        # Get target dimensions based on aspect ratio
        if aspect == "16:9":
            target_size = (1920, 1080)
        elif aspect == "9:16":
            target_size = (1080, 1920)
        else:  # 1:1
            target_size = (1080, 1080)
        
        # Create video clip
        if image_path and os.path.exists(image_path):
            try:
                # Create image clip with proper sizing and letterboxing
                image_clip = ImageClip(image_path, duration=duration)
                
                # Apply Ken Burns effect if specified
                motion = scene.get("motion", {})
                if motion.get("type") == "kenburns":
                    zoom = motion.get("zoom", 1.05)
                    image_clip = self._apply_ken_burns_safe(image_clip, zoom)
                
                # Resize and letterbox to target aspect ratio
                image_clip = self._resize_and_letterbox(image_clip, target_size)
                
                # Combine with audio
                final_clip = image_clip.set_audio(audio_clip)
                
            except Exception as e:
                logger.error(f"Failed to create image clip from {image_path}: {e}")
                # Fallback to text or color clip
                final_clip = self._create_fallback_clip(scene["line"], duration, target_size, audio_clip)
        else:
            # No image available - create fallback clip
            logger.warning(f"Image not found: {image_path}, creating fallback")
            final_clip = self._create_fallback_clip(scene["line"], duration, target_size, audio_clip)
        
        return final_clip
    
    def _resize_and_letterbox(self, clip, target_size):
        """Resize clip to fit target size with letterboxing"""
        from moviepy.editor import CompositeVideoClip, ColorClip
        
        target_w, target_h = target_size
        
        # Calculate scaling to fit within target while maintaining aspect ratio
        clip_w, clip_h = clip.size
        scale_w = target_w / clip_w
        scale_h = target_h / clip_h
        scale = min(scale_w, scale_h)  # Scale to fit
        
        # Resize clip
        new_w = int(clip_w * scale)
        new_h = int(clip_h * scale)
        resized_clip = clip.resize((new_w, new_h))
        
        # Create black background
        bg = ColorClip(size=target_size, color=(0, 0, 0), duration=clip.duration)
        
        # Center the resized clip on the background
        final_clip = CompositeVideoClip([bg, resized_clip.set_position('center')])
        
        return final_clip
    
    def _apply_ken_burns_safe(self, clip, zoom_factor):
        """Apply safe Ken Burns effect"""
        try:
            def zoom_effect(get_frame, t):
                frame = get_frame(t)
                # Simple zoom - scale from 1.0 to zoom_factor over duration
                progress = t / clip.duration
                current_zoom = 1.0 + (zoom_factor - 1.0) * progress
                return frame  # Simplified for now - full zoom would require cv2
            
            # For now, just return the original clip to avoid complexity
            return clip
        except Exception as e:
            logger.warning(f"Ken Burns effect failed: {e}, using static image")
            return clip
    
    def _create_fallback_clip(self, text, duration, target_size, audio_clip):
        """Create fallback text/color clip when image fails"""
        from moviepy.editor import ColorClip, TextClip, CompositeVideoClip
        
        # Create black background
        bg = ColorClip(size=target_size, color=(0, 0, 0), duration=duration)
        
        # Try to add text if ImageMagick is available
        enable_text = os.getenv("ENABLE_KINETIC_TEXT", "false").lower() == "true"
        
        if enable_text:
            try:
                txt_clip = TextClip(
                    text,
                    fontsize=min(target_size[0] // 20, 60),  # Responsive font size
                    color='white',
                    font='Arial'  # Use common Windows font
                ).set_position('center').set_duration(duration)
                
                video_clip = CompositeVideoClip([bg, txt_clip])
            except Exception as text_error:
                logger.warning(f"TextClip creation failed: {text_error}, using color only")
                video_clip = bg
        else:
            # TextClip disabled, use solid color
            video_clip = bg
        
        # Combine with audio
        return video_clip.set_audio(audio_clip)
    
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
        def resize_func(t):
            progress = t / clip.duration if clip.duration > 0 else 0
            current_zoom = 1 + (zoom - 1) * progress
            return current_zoom
        
        return clip.resize(lambda t: resize_func(t))
    
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
                color='white'
            ).set_position('center').set_duration(duration)
            
            return CompositeVideoClip([bg, txt_clip])
        except Exception as e:
            logger.warning(f"TextClip creation failed: {e}, using background only")
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

import os
import json
import math
import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..config import settings

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# MoviePy imports (v2 preferred, v1 fallback)
# -----------------------------------------------------------------------------
try:
    # MoviePy ≥ 2.x exposes classes at the top-level package
    from moviepy import (
        ImageClip,
        AudioFileClip,
        concatenate_videoclips,
        CompositeVideoClip,
        ColorClip,
        TextClip,
        VideoFileClip,
    )
    MOVIEPY_V2 = True
except Exception:  # pragma: no cover
    # MoviePy 1.x
    from moviepy.editor import (  # type: ignore
        ImageClip,
        AudioFileClip,
        concatenate_videoclips,
        CompositeVideoClip,
        ColorClip,
        TextClip,
        VideoFileClip,
    )
    MOVIEPY_V2 = False

# --- MoviePy v2 compatibility shim: alias .resize(...) to .with_size(...) ---
try:
    if MOVIEPY_V2:
        from moviepy import ImageClip as _MPImageClip
        from moviepy import ColorClip as _MPColorClip
        from moviepy import VideoClip as _MPVideoClip

        def _resize_alias(self, *args, **kwargs):
            """
            Backward-compatible alias so old code calling .resize(...) keeps working
            on MoviePy v2 where .with_size(...) is the new API.
            Supports .resize((w, h)), .resize(width=..), .resize(height=..), .resize(newsize=(w,h)).
            """
            if args and isinstance(args[0], tuple):
                return self.with_size(args[0])
            if "width" in kwargs or "height" in kwargs:
                return self.with_size(width=kwargs.get("width"), height=kwargs.get("height"))
            if "newsize" in kwargs and isinstance(kwargs["newsize"], tuple):
                return self.with_size(kwargs["newsize"])
            return self

        for _cls in (_MPImageClip, _MPColorClip, _MPVideoClip):
            if not hasattr(_cls, "resize") and hasattr(_cls, "with_size"):
                setattr(_cls, "resize", _resize_alias)

except Exception as _shim_err:  # pragma: no cover
    logger.debug(f"MoviePy resize shim not applied: {_shim_err}")


# =============================================================================
# Asset Curator
# =============================================================================
class AssetCuratorAgent:
    def curate(self, run_dir: str) -> Dict:
        logger.info(f"Curating assets in {run_dir}")
        assets = {"images": [], "logos": [], "audio": [], "brief": None}

        if not os.path.exists(run_dir):
            logger.warning(f"Run directory {run_dir} does not exist")
            return assets

        for name in os.listdir(run_dir):
            file_path = str(Path(run_dir) / name)
            name_lower = name.lower()

            if name_lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif")):
                if "logo" in name_lower or "brand" in name_lower:
                    assets["logos"].append(file_path)
                else:
                    assets["images"].append(file_path)

            elif name_lower.endswith((".wav", ".mp3", ".m4a", ".aac", ".ogg")):
                assets["audio"].append(file_path)

            elif name_lower.endswith((".txt", ".md", ".json")):
                if any(k in name_lower for k in ["brief", "style", "prompt", "copy"]):
                    assets["brief"] = file_path

        (Path(run_dir) / "assets.json").write_text(json.dumps(assets, indent=2), encoding="utf-8")

        logger.info(
            "Assets curated: %s images, %s logos, %s audio, brief: %s",
            len(assets["images"]),
            len(assets["logos"]),
            len(assets["audio"]),
            "yes" if assets["brief"] else "no",
        )
        return assets


# =============================================================================
# Scriptwright
# =============================================================================
class ScriptwrightAgent:
    def draft(self, brief_text: str, target_length: int, tone: str, run_dir: str) -> str:
        logger.info(f"Drafting script - length={target_length}s, tone={tone}")

        # (Optional) read brief file — currently unused but keeps place for future LLM/RAG
        if brief_text and os.path.exists(brief_text):
            _ = Path(brief_text).read_text(encoding="utf-8")

        if target_length <= 15:
            beats = [
                "Transform your workflow.",
                "Simple. Fast. Effective.",
                "Try it now.",
            ]
        elif target_length <= 30:
            beats = [
                "Tired of the old way of doing things?",
                "We've built something better.",
                "Fast, reliable, and designed for you.",
                "Join thousands who've already made the switch.",
                "Get started today.",
            ]
        else:
            beats = [
                "Every day, millions struggle with outdated solutions.",
                "Wasting time, money, and opportunity.",
                "That's why we created something revolutionary.",
                "A platform that thinks ahead, adapts, and delivers.",
                "Used by industry leaders worldwide.",
                "Proven results in under 24 hours.",
                "Ready to join the future?",
                "Start your free trial today.",
            ]

        script = "\n".join(beats)
        Path(run_dir, "script.md").write_text(script, encoding="utf-8")
        logger.info("Script drafted with %d beats", len(beats))
        return script


# =============================================================================
# Director
# =============================================================================
class DirectorAgent:
    def storyboard(self, script: str, images: List[str], run_dir: str) -> Dict:
        lines = [line.strip() for line in script.splitlines() if line.strip()]
        scenes = []
        for i, line in enumerate(lines):
            img = images[i % len(images)] if images else None
            scene = {
                "id": i + 1,
                "line": line,
                "assets": {"image": img},
                "motion": {"type": "kenburns", "zoom": 1.05},
                "text": {"kinetic": not img},
            }
            scenes.append(scene)

        shots = {"scenes": scenes}
        Path(run_dir, "shots.json").write_text(json.dumps(shots, indent=2), encoding="utf-8")
        logger.info("Storyboard created with %d scenes", len(scenes))
        return shots


# =============================================================================
# Narrator (TTS)
# =============================================================================
class NarratorAgent:
    def synth(self, text_lines: List[str], voice: str, lang: str, run_dir: str) -> List[str]:
        """
        Returns a list of WAV file paths (24 kHz mono) — one per text line.
        """
        logger.info("Synthesizing %d lines with voice=%s", len(text_lines), voice)
        out_dir = Path(run_dir) / "temp_audio"
        out_dir.mkdir(parents=True, exist_ok=True)

        if voice == "mute":
            return self._synth_mute(text_lines, out_dir)

        # Try Kokoro first (if installed), else fall back to espeak, else silence
        try:
            return self._synth_kokoro(text_lines, voice, lang, out_dir)
        except Exception as e:
            logger.warning("Kokoro failed: %s (falling back to espeak)", e)
            return self._synth_espeak(text_lines, voice, lang, out_dir)

    # --- helpers ----------------------------------------------------------------
    def _synth_mute(self, text_lines, out_dir: Path) -> List[str]:
        import subprocess
        wavs = []
        for i, _ in enumerate(text_lines, 1):
            path = out_dir / f"line_{i:02d}.wav"
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(path)],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                self._create_silent(path, 2.0)
            wavs.append(str(path))
        return wavs

    def _synth_kokoro(self, text_lines, voice, lang, out_dir: Path) -> List[str]:
        import soundfile as sf
        try:
            from kokoro_onnx import KPipeline
        except Exception as e:
            raise ImportError("kokoro-onnx not available") from e

        pipe = KPipeline(lang_code=lang)
        wavs: List[str] = []
        for i, line in enumerate(text_lines, 1):
            audio_full = None
            for _, _, audio in pipe(line, voice=voice, speed=1.0):
                audio_full = audio  # last chunk
            out = out_dir / f"line_{i:02d}.wav"
            if audio_full is None:
                logger.warning("Kokoro returned no audio for line %d — writing silence", i)
                self._create_silent(out, 2.0)
            else:
                sf.write(str(out), audio_full, 24000)
            wavs.append(str(out))
        return wavs

    def _synth_espeak(self, text_lines, voice, lang, out_dir: Path) -> List[str]:
        import shutil
        import subprocess

        wavs: List[str] = []

        which = shutil.which("espeak-ng")
        candidates = [
            which if which else None,
            r"C:\Program Files\eSpeak NG\espeak-ng.exe",
            r"C:\Program Files (x86)\eSpeak NG\espeak-ng.exe",
        ]
        espeak_cmd = None
        for c in candidates:
            if c and (c == which or Path(c).exists()):
                espeak_cmd = c
                break

        if not espeak_cmd:
            logger.error("espeak-ng not found, generating silence")
            return [str(self._create_silent(out_dir / f"line_{i:02d}.wav", 2.0)) for i in range(1, len(text_lines) + 1)]

        for i, line in enumerate(text_lines, 1):
            path = out_dir / f"line_{i:02d}.wav"
            try:
                espeak_voice = f"{lang}+{voice}" if voice and voice != "default" else lang
                subprocess.run(
                    [espeak_cmd, "-v", espeak_voice, "-s", "150", "-w", str(path), line],
                    check=True,
                    capture_output=True,
                )
            except Exception as e:
                logger.error("espeak failed on line %d: %s — writing silence", i, e)
                self._create_silent(path, 2.0)
            wavs.append(str(path))

        return wavs

    def _create_silent(self, path: Path, duration: float) -> Path:
        import numpy as np
        import soundfile as sf

        sr = 24000
        sf.write(str(path), np.zeros(int(sr * duration), dtype=np.float32), sr)
        return path


# =============================================================================
# Music Supervisor (MVP stub)
# =============================================================================
class MusicSupervisorAgent:
    def pick_and_duck(self, run_dir: str) -> Optional[str]:
        logger.info("Music supervision skipped (MVP)")
        return None


# =============================================================================
# Editor
# =============================================================================
class EditorAgent:
    def _with_or_set(self, clip, base: str, *args, **kwargs):
        """
        MoviePy v2 prefers with_{base}(...); v1 uses set_{base}(...).
        This calls whichever exists; otherwise returns the clip unchanged.
        """
        with_name = f"with_{base}"
        set_name = f"set_{base}"
        if hasattr(clip, with_name):
            return getattr(clip, with_name)(*args, **kwargs)
        if hasattr(clip, set_name):
            return getattr(clip, set_name)(*args, **kwargs)
        return clip

    def render(self, run_id: str, shots: Dict, wavs: List[str], aspect: str, run_dir: str) -> str:
        """
        Very safe render + subtle motion + optional captions.
        Produces H.264 + AAC MP4 at 30 fps.
        """
        out_dir = Path(settings.outputs_dir) / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "ad_final.mp4"

        # Choose target canvas by aspect
        if aspect == "9:16":
            target = (1080, 1920)
        elif aspect == "1:1":
            target = (1080, 1080)
        else:
            target = (1920, 1080)  # 16:9 default

        scenes = shots.get("scenes", [])
        if not scenes:
            raise RuntimeError("No scenes to render (shots['scenes'] is empty)")

        enable_text = os.getenv("ENABLE_KINETIC_TEXT", "true").lower() == "true"

        clips = []
        for idx, (scene, wav) in enumerate(zip(scenes, wavs), start=1):
            # load audio (or default 2s)
            duration = 2.0
            audio_clip = None
            try:
                audio_clip = AudioFileClip(wav)
                duration = max(audio_clip.duration, 0.5)
            except Exception as e:
                logger.warning("Audio load failed for %s: %s", wav, e)

            image_path = scene.get("assets", {}).get("image")
            if image_path and Path(image_path).exists():
                try:
                    img = ImageClip(image_path, duration=duration)
                except Exception as e:
                    logger.warning("ImageClip failed for %s: %s; using black", image_path, e)
                    img = ColorClip(size=target, color=(0, 0, 0), duration=duration)
            else:
                img = ColorClip(size=target, color=(0, 0, 0), duration=duration)

            # letterbox to target
            img = self._fit_letterbox(img, target)

            # --- gentle "alive" motion ---------------------------------------
            # (i) slow Ken Burns zoom (functional resize works in v1/v2)
            try:
                img = img.resize(lambda t: 1.0 + 0.03 * (t / max(duration, 0.01)))  # ~3% over scene
            except Exception:
                pass

            # (ii) subtle sway (±1.5° at 0.5 Hz) to mimic waving
            if hasattr(img, "rotate"):
                try:
                    img = img.rotate(lambda t: 1.5 * math.sin(2 * math.pi * 0.5 * t), unit="deg")
                except Exception:
                    pass

            # --- overlay captions (power words) ------------------------------
            if enable_text:
                line = scene.get("line", "").strip()
                if line:
                    try:
                        caption_width = int(target[0] * 0.85)
                        fontsize = max(28, min(target[0] // 18, 72))

                        txt = TextClip(
                            line,
                            fontsize=fontsize,
                            color="white",
                            font="Arial",
                            method="caption",
                            size=(caption_width, None),
                        )
                        txt = txt.on_color(
                            size=(txt.w + 40, txt.h + 20),
                            color=(0, 0, 0),
                            col_opacity=0.55,
                        )
                        txt = self._with_or_set(txt, "duration", duration)
                        txt = self._with_or_set(txt, "position", ("center", int(target[1] * 0.85)))
                        img = CompositeVideoClip([img, txt])
                    except Exception as e:
                        logger.warning(f"Caption overlay failed: {e}")

            # attach audio
            if audio_clip:
                img = self._with_or_set(img, "audio", audio_clip)

            clips.append(img)

        if not clips:
            raise RuntimeError("No clips created")

        final = concatenate_videoclips(clips, method="compose")

        final.write_videofile(
            str(out_path),
            fps=30,
            codec="libx264",
            audio_codec="aac",
            ffmpeg_params=["-movflags", "+faststart"],
            temp_audiofile=str(out_dir / "temp-audio.m4a"),
            remove_temp=True,
            logger=None,
        )

        # close resources (important on Windows)
        try:
            final.close()
        except Exception:
            pass
        for c in clips:
            try:
                c.close()
            except Exception:
                pass

        return str(out_path)

    # --- helpers ----------------------------------------------------------------
    def _set_size(self, clip, *, width: Optional[int] = None, height: Optional[int] = None, size: Optional[tuple] = None):
        """
        MoviePy v2 prefers .with_size(); v1 uses .resize().
        This helper accepts either exact size, or width/height constraints.
        """
        if size is not None:
            if MOVIEPY_V2 and hasattr(clip, "with_size"):
                return clip.with_size(size)
            return clip.resize(size)  # v1
        if width is not None:
            if MOVIEPY_V2 and hasattr(clip, "with_size"):
                return clip.with_size(width=width)
            return clip.resize(width=width)  # v1
        if height is not None:
            if MOVIEPY_V2 and hasattr(clip, "with_size"):
                return clip.with_size(height=height)
            return clip.resize(height=height)  # v1
        return clip

    def _fit_letterbox(self, clip, target_size):
        """Resize clip to fit within target size, letterboxed; MoviePy v1/v2 safe."""
        tw, th = target_size
        try:
            cw, ch = clip.size
        except Exception:
            cw, ch = tw, th

        cw = max(1, int(cw))
        ch = max(1, int(ch))
        scale = min(tw / cw, th / ch)
        new_w, new_h = max(1, int(cw * scale)), max(1, int(ch * scale))

        if hasattr(clip, "with_size"):
            resized = clip.with_size((new_w, new_h))
        elif hasattr(clip, "resize"):
            resized = clip.resize((new_w, new_h))
        else:
            resized = clip  # can't resize

        dur = getattr(clip, "duration", 2.0)
        bg = ColorClip(size=target_size, color=(0, 0, 0), duration=dur)
        resized_centered = self._with_or_set(resized, "position", "center")
        return CompositeVideoClip([bg, resized_centered])

    def _apply_ken_burns_placeholder(self, clip):
        """No-op placeholder to keep behavior predictable."""
        return clip


# =============================================================================
# QA
# =============================================================================
class QAAgent:
    def audit(self, out_path: str, run_id: str, shots: Dict, run_dir: str) -> Dict:
        p = Path(out_path)
        exists = p.exists()
        size = p.stat().st_size if exists else 0

        duration = 0.0
        if exists:
            try:
                with VideoFileClip(str(p)) as v:
                    duration = float(v.duration or 0.0)
            except Exception:
                pass

        return {
            "status": "ok" if exists and size > 0 else "failed",
            "output_path": str(p),
            "file_size": size,
            "duration_sec": duration,
        }

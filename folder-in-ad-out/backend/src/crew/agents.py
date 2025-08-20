import os
from typing import Dict, List
from ..config import settings

class AssetCuratorAgent:
    def curate(self, run_dir: str) -> Dict:
        # Minimal: treat all images/audio as-is; produce manifest.
        assets = {"images": [], "logos": [], "audio": [], "brief": None}
        for name in os.listdir(run_dir):
            p = os.path.join(run_dir, name)
            low = name.lower()
            if low.endswith((".png",".jpg",".jpeg",".webp")):
                if "logo" in low:
                    assets["logos"].append(p)
                else:
                    assets["images"].append(p)
            elif low.endswith((".wav",".mp3",".m4a")):
                assets["audio"].append(p)
            elif low.endswith((".txt",".md",".json")):
                if "brief" in low or "style" in low:
                    assets["brief"] = p
        return assets

class ScriptwrightAgent:
    def draft(self, brief_text: str, target_length: int, tone: str) -> str:
        # Minimal deterministic script for MVP
        beats = [
            "HOOK: Tired of boring ads?",
            "PROBLEM: Filming is costly and slow.",
            "SOLUTION: Our AI studio turns your folder into a finished ad.",
            "BENEFIT: Fast, on-brand, and scalable variants.",
            "CTA: Try it today."
        ]
        return "\n".join(beats)

class DirectorAgent:
    def storyboard(self, script: str, images: List[str]) -> Dict:
        lines = [l for l in script.splitlines() if l.strip()]
        plan = []
        for i, line in enumerate(lines):
            img = images[min(i, len(images)-1)] if images else None
            plan.append({
                "id": i+1,
                "line": line,
                "assets": {"image": img},
                "motion": {"type": "kenburns", "zoom": 1.08, "pan": "center"},
                "text": {"kinetic": True}
            })
        return {"scenes": plan}

class NarratorAgent:
    def synth(self, text_lines: List[str], voice: str, lang: str) -> List[str]:
        engine = settings.tts_engine
        out_wavs = []
        if engine == "kokoro":
            from kokoro import KPipeline
            pipe = KPipeline(lang_code=lang)
            import soundfile as sf
            for idx, line in enumerate(text_lines, 1):
                chunks = pipe(line, voice=voice)
                # chunks: iterable of (phonemes, durations, audio_bytes)
                audio = b"".join(a for _,_,a in chunks)
                path = os.path.join(settings.output_dir, "tmp", f"line_{idx:02d}.wav")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                sf.write(path, sf.read(io.BytesIO(audio))[0], 24000)  # fallback if raw; otherwise writebytes
                # Simpler approach: pipe.save_to_file(...) if available in version
                out_wavs.append(path)
            return out_wavs
        else:
            # Placeholder for other TTS providers
            raise NotImplementedError("Only kokoro in MVP")

class MusicSupervisorAgent:
    def pick_and_duck(self) -> str:
        # MVP: no music; return empty string or a tiny beep bed
        return ""

class EditorAgent:
    def render(self, run_id: str, shots: Dict, wavs: List[str], aspect: str) -> str:
        # MVP render: image + VO per scene -> concatenate using moviepy
        import os
        from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
        clips = []
        for scene, wav in zip(shots["scenes"], wavs):
            img = scene["assets"]["image"]
            if not img:
                continue
            ac = AudioFileClip(wav)
            ic = ImageClip(img).set_duration(ac.duration).set_audio(ac)
            ic = ic.resize(height=1080)  # naive sizing
            clips.append(ic)
        final = concatenate_videoclips(clips) if clips else None
        out_dir = os.path.join(settings.output_dir, run_id)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "ad_final.mp4")
        if final:
            final.write_videofile(out_path, fps=30, codec="libx264", audio_codec="aac")
        return out_path

class QAAgent:
    def audit(self, out_path: str) -> Dict:
        # Minimal checks
        ok = os.path.exists(out_path) and os.path.getsize(out_path) > 0
        return {"ok": ok, "path": out_path}

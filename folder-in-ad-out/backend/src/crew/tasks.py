import os, json
from typing import Dict
from .agents import (
    AssetCuratorAgent, ScriptwrightAgent, DirectorAgent,
    NarratorAgent, MusicSupervisorAgent, EditorAgent, QAAgent
)
from ..api.utils import write_json
from ..config import settings

def task_curate(run_dir: str) -> Dict:
    curator = AssetCuratorAgent()
    assets = curator.curate(run_dir)
    write_json(os.path.join(run_dir, "assets.json"), assets)
    return assets

def task_script(assets: Dict, target_length: int, tone: str) -> str:
    brief_text = ""
    if assets.get("brief"):
        with open(assets["brief"], "r", encoding="utf-8") as f:
            brief_text = f.read()
    s = ScriptwrightAgent().draft(brief_text, target_length, tone)
    return s

def task_direct(script: str, assets: Dict) -> Dict:
    shots = DirectorAgent().storyboard(script, assets.get("images", []))
    return shots

def task_tts(shots: Dict, voice: str, lang: str) -> list:
    lines = [s["line"] for s in shots["scenes"]]
    wavs = NarratorAgent().synth(lines, voice=voice, lang=lang)
    return wavs

def task_edit(run_id: str, shots: Dict, wavs: list, aspect: str) -> str:
    path = EditorAgent().render(run_id, shots, wavs, aspect)
    return path

def task_qa(path: str) -> Dict:
    return QAAgent().audit(path)

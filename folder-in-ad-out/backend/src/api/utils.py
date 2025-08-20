import os, json, subprocess, tempfile
from typing import Dict, List
from ..config import settings

def ffmpeg_exists() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def write_json(path: str, obj: Dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def read_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def safe_filename(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in ("-", "_", ".")).rstrip()

def concat_audio_wavs(wavs: List[str], out_wav: str):
    # naive concat with ffmpeg
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as f:
        for w in wavs:
            f.write(f"file '{os.path.abspath(w)}'\n")
        flist = f.name
    subprocess.check_call(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", flist, "-c", "copy", out_wav])

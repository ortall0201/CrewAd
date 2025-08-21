# CrewAd Runbook

Quick reference for running and testing the CrewAd pipeline.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11
- FFmpeg installed and in PATH
- eSpeak NG installed

### 2. Backend Setup
```bash
cd folder-in-ad-out/backend
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Start Server
```bash
cd folder-in-ad-out/backend
.venv\Scripts\activate
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start Frontend (separate terminal)
```bash
cd folder-in-ad-out/frontend
python -m http.server 3000
```

## 🧪 Testing

### Automated Smoke Test
```bash
cd folder-in-ad-out/backend
.venv\Scripts\activate
python -m src.cli.smoke
```

### Manual API Testing

1. **Upload Assets**:
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "files=@test-files/test-image.png" \
  -F "files=@test-files/brief.txt"
```

2. **Start Pipeline** (use run_id from step 1):
```bash
curl -X POST http://localhost:8000/api/run \
  -F "run_id=YOUR_RUN_ID" \
  -F "target_length=15" \
  -F "tone=confident" \
  -F "voice=default" \
  -F "aspect=16:9"
```

3. **Monitor Status**:
```bash
curl http://localhost:8000/api/status/YOUR_RUN_ID
```

4. **Download Video**:
```bash
curl http://localhost:8000/api/download/YOUR_RUN_ID -o final_ad.mp4
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## 📊 Expected Results

### Successful Pipeline
```json
{
  "success": true,
  "run_id": "abc-123",
  "video_path": "C:\\...\\outputs\\abc-123\\ad_final.mp4",
  "metadata": {
    "status": "ok",
    "file_exists": true,
    "file_size": 23301,
    "duration": 6.0
  }
}
```

### Pipeline Steps
1. **Curate**: Asset categorization (~1s)
2. **Script**: AI copywriting (~1s) 
3. **Direct**: Storyboard creation (~1s)
4. **Narrate**: TTS generation (~3s)
5. **Music**: Audio supervision (~1s)
6. **Edit**: Video rendering (~10s)
7. **QA**: Quality validation (~1s)

**Total Time**: ~18 seconds for typical 3-scene video

## 🔧 Configuration

### Environment Variables (.env)
```bash
# TTS Configuration
TTS_PROVIDER=kokoro
KOKORO_LANG=en
KOKORO_VOICE=af_heart

# Feature Flags
ENABLE_KINETIC_TEXT=true
RAG_ENABLED=true

# Video Settings  
VIDEO_FPS=30
VIDEO_CODEC=libx264
AUDIO_CODEC=aac

# Paths
FFMPEG_BINARY=ffmpeg
IMAGEMAGICK_BINARY=magick
```

### Supported Parameters
- **Tones**: confident, friendly, professional, casual, urgent, calm
- **Voices**: default, af_heart, various espeak voices
- **Aspects**: 16:9, 9:16, 1:1
- **Lengths**: 5-120 seconds

## 🐛 Troubleshooting

### Common Issues

**"FFmpeg not found"**
```bash
# Test FFmpeg
ffmpeg -version

# Windows install
choco install ffmpeg
```

**"eSpeak NG not found"**
```bash  
# Test eSpeak
espeak-ng --version

# Windows install
choco install espeak
```

**"Video not created"**
```bash
# Check pipeline logs
cat folder-in-ad-out/outputs/{RUN_ID}/pipeline.log

# Debug video rendering directly
cd folder-in-ad-out/backend
python debug_editor.py
```

**"Pipeline failed"**
- Check server logs in terminal
- Verify all system dependencies installed
- Ensure sufficient disk space
- Try with smaller images (<2MB)

**JSON API not working**
- Use form data API instead: `/api/run` with form parameters
- Check Content-Type header is correct for JSON
- Verify request body format matches schema

### Debug Scripts
```bash
cd folder-in-ad-out/backend

# Test video rendering specifically
python debug_editor.py

# Test full pipeline execution  
python debug_pipeline.py

# Check dependencies
python -c "import moviepy, chromadb, soundfile; print('All imports OK')"
```

## 📁 File Structure

### Inputs (uploads/{run_id}/)
- User images (JPG, PNG, etc.)
- Brief text files
- Optional audio files
- Generated: assets.json, script.md, shots.json

### Outputs (outputs/{run_id}/)
- ad_final.mp4 (final video)
- pipeline.log (detailed logs)
- temp_audio/ (intermediate audio files)

## ⚡ Performance Tips

- **Images**: Keep under 2MB for faster processing
- **Length**: Shorter videos (10-30s) process faster
- **Disk Space**: Ensure 100MB+ free space per video
- **Memory**: 4GB+ RAM recommended for video rendering

## 🎬 Expected Output Quality

- **Resolution**: 1920x1080 (16:9), 1080x1920 (9:16), 1080x1080 (1:1)
- **Codec**: H.264/libx264 with AAC audio
- **Frame Rate**: 30 FPS
- **File Size**: ~20-50KB for typical 6-second video
- **Motion**: Ken Burns effects on static images
- **Audio**: Clear TTS narration with proper timing

---

**Need Help?** Check the full README.md or docs/ADR-001-hybrid-agentic-media.md for detailed architecture information.
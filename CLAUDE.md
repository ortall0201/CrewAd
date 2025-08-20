# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend Setup and Running
```bash
# Setup (run once)
cd folder-in-ad-out/backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install fastapi uvicorn python-multipart pydantic-settings soundfile moviepy chromadb sentence-transformers

# Start development server
cd folder-in-ad-out/backend
.venv\Scripts\python.exe -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Test API health
curl http://localhost:8000/health
```

### Frontend Setup and Running  
```bash
# Start frontend (separate terminal)
cd folder-in-ad-out/frontend
python -m http.server 3000
```

### System Dependencies Required
- **ffmpeg**: Required for video processing (MoviePy backend)
- **espeak-ng**: Required for TTS fallback when Kokoro TTS unavailable
- Both must be installed and accessible in PATH before running

## Architecture Overview

### Multi-Agent AI Pipeline
CrewAd uses a 7-step sequential pipeline orchestrated through specialized AI agents:

1. **AssetCuratorAgent** (`src/crew/agents.py:10-50`) - Scans uploads, categorizes files into images/logos/audio/briefs, generates `assets.json`
2. **ScriptwrightAgent** - Creates ad copy using RAG-enhanced prompts from brand tone guidelines
3. **DirectorAgent** - Maps script lines to visual assets, creates shot sequences with motion planning
4. **NarratorAgent** - Generates TTS audio using Kokoro or espeak-ng fallback 
5. **MusicSupervisorAgent** - Handles background audio (currently MVP stub)
6. **EditorAgent** - Assembles final video using MoviePy with Ken Burns effects
7. **QAAgent** - Validates output quality and generates metadata

### File Contract System
The pipeline maintains strict JSON contracts between agents:

- **`assets.json`**: File categorization manifest with absolute paths
- **`script.md`**: Generated ad copy optimized for target length/tone
- **`shots.json`**: Shot sequences mapping script lines to assets with motion data
- **`metadata.json`**: Final video metadata including LUFS, duration, render stats

### Configuration System
Settings managed through Pydantic Settings (`src/config.py`) with `.env` file override:

**Key Settings:**
- `TTS_PROVIDER`: "kokoro" (default) or "espeak" 
- `RAG_ENABLED`: Enables brand tone guidance system
- `VIDEO_FPS`: Frame rate for output (default: 30)
- `KOKORO_MODEL/LANG/VOICE`: TTS model configuration

### RAG (Retrieval-Augmented Generation)
Brand-safe copywriting system using ChromaDB vector store:

- **Knowledge Base**: `src/rag/documents/` contains brand tone guidelines and video structure rules
- **Vector Store**: `src/rag/index_db/` (auto-generated)
- **Integration**: Agents query knowledge base for contextually appropriate copy generation

### Status Tracking System
Thread-safe in-memory status tracking (`src/crew/run_crew.py:15-44`):

- **Status Store**: `_RUNS` dictionary with threading locks
- **Real-time Updates**: Each agent reports progress via `_set_status()`
- **Frontend Polling**: `/api/status/{run_id}` endpoint polled every 2s
- **Production Note**: Replace with Redis for multi-instance deployment

### API Architecture
FastAPI backend (`src/api/routes.py`) with async background processing:

**Core Endpoints:**
- `POST /api/upload` - File validation, run_id generation, asset storage
- `POST /api/run` - Pipeline trigger with parameter validation, background task queuing  
- `GET /api/status/{run_id}` - Real-time pipeline status
- `GET /api/download/{run_id}` - Final video file delivery

**File Validation**: Strict MIME type checking for images (`ALLOWED_IMAGE_TYPES`), audio (`ALLOWED_AUDIO_TYPES`), text (`ALLOWED_TEXT_TYPES`)

### Directory Structure
```
uploads/{run_id}/     # User-provided assets
├── image1.jpg
├── logo.png  
├── brief.txt
└── assets.json      # Generated manifest

outputs/{run_id}/    # Generated content
└── ad_final.mp4     # Final video output
```

## Development Workflow

### Adding New Agents
1. Create agent class in `src/crew/agents.py` following existing patterns
2. Add corresponding task class in `src/crew/tasks.py` 
3. Integrate into pipeline sequence in `src/crew/run_crew.py:74-187`
4. Update status tracking and frontend step labels

### Modifying File Contracts
All intermediate files use strict JSON schemas. Changes require:
1. Update contract documentation in agent docstrings
2. Modify both producing and consuming agents
3. Test full pipeline end-to-end

### Configuration Changes
Environment variables automatically loaded via Pydantic Settings. Add new settings to:
1. `src/config.py` Settings class
2. `.env.template` with documentation
3. Update startup validation in `src/main.py:17-47` if required

### RAG Knowledge Updates
1. Add/modify documents in `src/rag/documents/`
2. Vector store rebuilds automatically on startup
3. Test agent queries return expected guidance

## Testing Strategy

Since no formal test suite exists, manual testing workflow:

1. **Unit Testing**: Test individual agents with sample `run_dir` inputs
2. **Integration Testing**: Run full pipeline with various asset combinations
3. **API Testing**: Use `curl` or Postman for endpoint validation
4. **Frontend Testing**: Upload various file types, monitor status updates

## Common Development Issues

### Pipeline Failures
- Check system dependencies (ffmpeg, espeak-ng) are in PATH
- Verify file permissions in uploads/outputs directories  
- Monitor logs for agent-specific errors during processing
- Ensure sufficient disk space for video rendering

### TTS Issues
- Kokoro TTS may fail on first run due to model downloads
- System falls back to espeak-ng automatically
- Check `TTS_PROVIDER` setting if voice quality issues occur

### Memory Usage
- Large image files increase processing time and memory usage
- Consider resizing inputs to 1920x1080 maximum
- Monitor RAM usage during video rendering step
- Sentence transformers and ChromaDB use significant memory

### CORS Issues
Frontend served from different port requires CORS configuration in `src/main.py:76-83`. Currently set to allow all origins for development.
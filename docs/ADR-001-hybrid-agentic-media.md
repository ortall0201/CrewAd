# ADR-001: Hybrid Agentic Media Architecture

**Status**: Accepted  
**Date**: 2025-08-21  
**Authors**: Senior Engineer Audit  

## Context

CrewAd needed a video generation pipeline that could handle complex creative decisions while ensuring deterministic, reliable media processing on Windows systems. The challenge was balancing AI-driven creative decisions with robust media rendering.

## Decision

We adopted a **hybrid agentic media architecture** that separates creative reasoning from deterministic media processing:

### Creative Layer (AI Agents)
- **AssetCuratorAgent**: Intelligent file categorization and validation
- **ScriptwrightAgent**: RAG-enhanced copywriting with brand tone guidance  
- **DirectorAgent**: Scene composition and motion planning
- **NarratorAgent**: Voice synthesis orchestration with fallback logic
- **MusicSupervisorAgent**: Audio supervision (MVP stub)
- **QAAgent**: Quality validation and metadata generation

### Deterministic Layer (Rendering Workers)
- **EditorAgent**: Bulletproof MoviePy/FFmpeg video rendering
- **Windows-safe file handling**: Proper path quoting, resource cleanup
- **Codec standardization**: Fixed libx264/AAC output for compatibility
- **Aspect ratio handling**: Letterboxing and scaling for consistent output

## Rationale

### Why Agents for Creative Tasks
1. **Contextual Decision Making**: Agents can reason about tone, brand guidelines, and artistic choices
2. **RAG Integration**: Can incorporate style guidance and brand safety rules
3. **Flexible Orchestration**: Easy to modify creative logic without touching rendering code
4. **Error Recovery**: Can make alternative creative choices when assets are missing

### Why Deterministic Workers for Media Processing
1. **Reliability**: Media processing requires deterministic, tested pipelines
2. **Performance**: No LLM overhead for computational tasks
3. **Debugging**: Easier to debug codec issues, file locks, and system integration
4. **Windows Compatibility**: Direct control over FFmpeg parameters and file handling

## Technical Implementation

### File Contracts
Strict JSON contracts ensure reliable data flow between creative and deterministic layers:

```
uploads/{run_id}/
├── assets.json      # AI: File categorization
├── script.md        # AI: Generated copy  
├── shots.json       # AI: Scene planning
├── temp_audio/      # Deterministic: Audio files
└── metadata.json    # AI: Quality assessment

outputs/{run_id}/
├── ad_final.mp4     # Deterministic: Final render
└── pipeline.log     # Deterministic: Detailed logging
```

### Agent Orchestration
```python
# Creative decisions with AI reasoning
assets = curator.curate(run_dir)              # AI categorization
script = scriptwright.draft(brief, tone)      # AI copywriting  
shots = director.storyboard(script, assets)   # AI scene planning
wavs = narrator.synth(lines, voice)           # AI voice orchestration

# Deterministic rendering
video_path = editor.render(shots, wavs, aspect)  # Deterministic MoviePy
qa_result = qa.audit(video_path, metadata)       # AI quality validation
```

### Windows-Safe Rendering
```python
# Bulletproof FFmpeg integration
from imageio_ffmpeg import get_ffmpeg_exe
os.environ["IMAGEIO_FFMPEG_EXE"] = get_ffmpeg_exe()

# Safe video rendering with proper cleanup
final_video.write_videofile(
    out_path,
    fps=30,
    codec="libx264", 
    audio_codec="aac",
    ffmpeg_params=["-movflags", "+faststart"],
    temp_audiofile=os.path.join(temp_dir, "temp-audio.m4a"),
    remove_temp=True
)
```

## Consequences

### Positive
- **Separation of Concerns**: Creative logic separate from media processing
- **Reliability**: Deterministic rendering with AI creative guidance
- **Maintainability**: Easy to modify creative behavior without affecting video quality
- **Windows Compatibility**: Robust file handling and codec management
- **Scalability**: Can replace individual agents without affecting the pipeline
- **Debugging**: Clear separation between creative failures and rendering failures

### Negative  
- **Complexity**: Two different paradigms in one system
- **Integration Points**: JSON contracts must be maintained carefully
- **Learning Curve**: Developers need to understand both AI and media processing domains

### Risks Mitigated
- **File Locks on Windows**: Proper resource cleanup in deterministic layer
- **Creative Failures**: Agents can make fallback decisions for missing assets
- **Codec Issues**: Standardized rendering parameters with Windows-tested paths
- **Status Tracking**: Per-run logging captures both creative and technical issues

## Alternatives Considered

1. **Pure Agent Architecture**: Would have required agents to understand FFmpeg intricacies
2. **Pure Deterministic Pipeline**: Would lack creative decision-making capabilities  
3. **Microservices**: Overkill for single-machine deployment, added network complexity

## Implementation Status

- ✅ All 7 agents implemented with proper creative reasoning
- ✅ Windows-safe EditorAgent with bulletproof MoviePy integration  
- ✅ File contracts established and documented
- ✅ Per-run logging with detailed error capture
- ✅ End-to-end testing with smoke test CLI
- ✅ 6-second videos successfully generated from image + brief inputs

## Future Evolution

- **Agent Improvements**: Enhanced creative reasoning with better LLMs
- **Rendering Optimization**: GPU acceleration for Ken Burns effects
- **Production Scaling**: Replace in-memory status with Redis for multi-instance deployment
- **Creative Expansion**: Add more sophisticated motion graphics and transitions
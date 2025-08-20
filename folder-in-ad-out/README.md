# Folder-in, Ad-out 

🎬 **AI-native ad studio**: Transform your folder of images into compelling video ads with AI.

Upload still images, optional logo, optional audio, and a brief style description. Our CrewAI-like pipeline validates assets, drafts scripts, maps sentences to images, generates voiceover, applies Ken Burns motion effects, and renders a final MP4 with metadata.

## ✨ Features

- **Drag & Drop Upload**: Simple web interface for uploading assets
- **AI Script Generation**: Creates compelling ad copy based on your brief and target specifications  
- **Smart Asset Mapping**: Intelligently maps script lines to visual assets
- **Multi-TTS Support**: Kokoro-82M TTS (default) with espeak-ng fallback
- **Ken Burns Effects**: Professional motion graphics for static images
- **Real-time Pipeline Status**: Live updates as your ad is being generated
- **Multiple Aspect Ratios**: 16:9, 9:16, and 1:1 support
- **RAG-Enhanced Copywriting**: Style guidance system for brand-safe content

## 🏗️ Architecture

```
/folder-in-ad-out
├── /backend              # FastAPI server
│   ├── /src
│   │   ├── main.py       # FastAPI app with dependency validation  
│   │   ├── config.py     # Environment configuration
│   │   ├── /api          # REST API endpoints
│   │   ├── /crew         # AI pipeline (agents, tasks, orchestration)
│   │   └── /rag          # Style guidance system
│   ├── requirements.txt
│   └── .env.template
├── /frontend             # Plain React UI
│   ├── index.html
│   ├── App.js           # Upload, configure, and status components
│   └── index.js
├── /uploads             # Uploaded assets (auto-created)
├── /outputs             # Generated videos (auto-created)  
└── README.md
```

## 🚀 Quick Start

### Prerequisites

Before running the application, ensure you have:

1. **Python 3.8+** installed
2. **ffmpeg** installed and accessible in PATH
3. **espeak-ng** installed (for TTS fallback)

#### Installing System Dependencies

**macOS (using Homebrew):**
```bash
brew install ffmpeg espeak-ng
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg espeak-ng
```

**Windows:**
- Install ffmpeg: Download from https://ffmpeg.org/download.html
- Install espeak-ng: Download from https://github.com/espeak-ng/espeak-ng/releases
- Add both to your system PATH

### Backend Setup

1. **Clone and navigate to the project:**
```bash
cd folder-in-ad-out/backend
```

2. **Create virtual environment:**
```bash
python -m venv .venv
```

3. **Activate virtual environment:**
```bash
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

4. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

5. **Configure environment (optional):**
```bash
cp .env.template .env
# Edit .env if you want to customize settings
```

6. **Start the backend server:**
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd ../frontend
```

2. **Serve the frontend:**

**Option A - Using Python (simple):**
```bash
python -m http.server 3000
```

**Option B - Using Node.js (if you have it):**
```bash
npx serve -s . -p 3000
```

**Option C - Using any static file server of your choice**

The frontend will be available at `http://localhost:3000`

## 📋 Usage

### Step 1: Upload Assets
- Drag and drop or click to select files
- **Supported formats:**
  - **Images**: JPG, PNG, WebP, GIF, BMP
  - **Audio**: WAV, MP3, M4A, AAC, OGG  
  - **Text**: TXT, MD, JSON (for briefs/style guides)
- Files are automatically categorized (images, logos, audio, briefs)

### Step 2: Configure Generation
- **Target Length**: 5-120 seconds
- **Tone**: Confident, Friendly, Professional, Casual, Urgent, Calm
- **Voice**: Default (Kokoro) or system fallback
- **Aspect Ratio**: 16:9 (landscape), 9:16 (portrait), 1:1 (square)

### Step 3: Generate & Download
- Click "Generate Ad" to start the pipeline
- Monitor real-time progress through 7 pipeline stages
- Download your finished MP4 when complete

## 🔧 Pipeline Stages

The AI pipeline consists of 7 stages:

1. **Asset Curation** - Scans and categorizes uploaded files
2. **Script Generation** - Creates compelling ad copy using RAG-enhanced prompts
3. **Storyboard Creation** - Maps script lines to visual assets with motion planning
4. **Voice Synthesis** - Generates TTS audio using Kokoro or espeak-ng fallback
5. **Music Supervision** - (MVP: placeholder for future background music)
6. **Video Rendering** - Assembles clips with Ken Burns effects using MoviePy
7. **Quality Assurance** - Validates output and generates metadata

## 📁 File Contracts

The system maintains strict file contracts for modularity:

### `assets.json`
```json
{
  "images": ["/abs/path/to/image1.jpg", "/abs/path/to/image2.png"],
  "logos": ["/abs/path/to/logo.png"], 
  "audio": ["/abs/path/to/music.wav"],
  "brief": "/abs/path/to/brief.txt"
}
```

### `script.md`
```
Hook line to grab attention
Problem identification  
Solution presentation
Benefit demonstration
Clear call-to-action
```

### `shots.json`  
```json
{
  "scenes": [
    {
      "id": 1,
      "line": "Hook line to grab attention",
      "assets": {"image": "/abs/path/to/image1.jpg"},
      "motion": {"type": "kenburns", "zoom": 1.08, "pan": "center"},
      "text": {"kinetic": true}
    }
  ]
}
```

### `metadata.json`
```json
{
  "run_id": "uuid",
  "duration_sec": 28.5,
  "voice": "kokoro_default", 
  "aspect": "16:9",
  "loudness_lufs": -23,
  "scenes": [...],
  "captions_file": null,
  "render_file": "ad_final.mp4"
}
```

## 🎛️ Configuration

Key environment variables (see `.env.template`):

- `TTS_PROVIDER`: "kokoro" (default) or "espeak"
- `VIDEO_FPS`: Frame rate (default: 30)
- `RAG_ENABLED`: Enable style guidance system
- `DEBUG`: Enable debug logging

## 🛠️ Development

### Running Tests
```bash
cd backend
pytest
```

### API Documentation
Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key API Endpoints
- `POST /api/upload` - Upload files, returns run_id
- `POST /api/run` - Start pipeline with parameters
- `GET /api/status/{run_id}` - Get pipeline status
- `GET /api/download/{run_id}` - Download generated video

## 🔍 Troubleshooting

### Common Issues

**"ffmpeg not found"**
- Ensure ffmpeg is installed and in your system PATH
- Test with: `ffmpeg -version`

**"espeak-ng not found"**  
- Install espeak-ng for TTS fallback support
- Test with: `espeak-ng --version`

**"Module 'kokoro' not found"**
- The Kokoro TTS package might not be available
- The system will automatically fall back to espeak-ng

**"ChromaDB import error"**
- RAG features will be disabled but core functionality remains
- Install with: `pip install chromadb`

**Upload fails**
- Check file types are supported
- Ensure backend is running on port 8000
- Check browser developer console for errors

### Performance Notes

- First run may be slower due to model loading
- Video rendering time depends on length and complexity
- Large image files will increase processing time
- Consider resizing images to 1920x1080 max for faster processing

## 🔮 Future Extensions  

The modular architecture supports easy extension:

- **A/B Testing**: Multiple script variants per run
- **Advanced TTS**: OpenAI, ElevenLabs, Azure integrations
- **Music Integration**: Auto-ducking background tracks
- **Brand Guidelines**: Company-specific style enforcement
- **Batch Processing**: Multiple ads from single asset folder
- **Video Templates**: Pre-designed motion and styling
- **Advanced Analytics**: Performance tracking and optimization

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines and submit pull requests for any improvements.

---

**Built with**: FastAPI, React, MoviePy, Kokoro TTS, ChromaDB
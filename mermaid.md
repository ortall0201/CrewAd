# CrewAd Flow Diagram

This Mermaid diagram illustrates the complete user journey from file upload to video download in the CrewAd AI-native ad studio.

```mermaid
graph TD
    %% User Actions
    User[👤 User] --> Upload[📁 Upload Files<br/>Drag & Drop]
    Upload --> Config[⚙️ Configure Parameters<br/>Length: 30s<br/>Tone: confident<br/>Aspect: 16:9]
    
    %% Frontend Components
    Upload --> UploadForm[🌐 UploadForm Component]
    Config --> RunButton[🌐 RunAgentButton Component]
    
    %% API Endpoints
    UploadForm --> |POST /api/upload| UploadAPI[📡 Upload Handler]
    RunButton --> |POST /api/run| RunAPI[📡 Run Handler]
    RunButton --> |GET /api/status/{id}| StatusAPI[📡 Status Handler]
    RunButton --> |GET /api/download/{id}| DownloadAPI[📡 Download Handler]
    
    %% Backend Processing
    UploadAPI --> FileValidation{🔍 Validate Files<br/>Images/Audio/Text}
    FileValidation --> |Valid| SaveFiles[💾 Save to uploads/{run_id}/]
    FileValidation --> |Invalid| Reject[❌ Reject Files]
    SaveFiles --> ReturnRunID[📋 Return run_id]
    
    RunAPI --> ValidateParams{✅ Validate Parameters}
    ValidateParams --> |Valid| BackgroundTask[🔄 Queue Background Task]
    ValidateParams --> |Invalid| ParamError[❌ Parameter Error]
    
    %% CrewAI Pipeline
    BackgroundTask --> Pipeline[🤖 AdCreationPipeline]
    
    Pipeline --> Step1[1️⃣ CURATE<br/>AssetCuratorAgent<br/>Categorize files]
    Step1 --> Step2[2️⃣ SCRIPT<br/>ScriptwrightAgent<br/>Generate ad copy]
    Step2 --> Step3[3️⃣ DIRECT<br/>DirectorAgent<br/>Create storyboard]
    Step3 --> Step4[4️⃣ NARRATE<br/>NarratorAgent<br/>Kokoro TTS synthesis]
    Step4 --> Step5[5️⃣ MUSIC<br/>MusicSupervisorAgent<br/>Background audio]
    Step5 --> Step6[6️⃣ EDIT<br/>EditorAgent<br/>MoviePy + ffmpeg]
    Step6 --> Step7[7️⃣ QA<br/>QAAgent<br/>Quality validation]
    
    %% Status Updates
    Step1 --> |Update Status| StatusStore[(🗄️ In-Memory Status Store<br/>Thread-safe with locks)]
    Step2 --> |Update Status| StatusStore
    Step3 --> |Update Status| StatusStore
    Step4 --> |Update Status| StatusStore
    Step5 --> |Update Status| StatusStore
    Step6 --> |Update Status| StatusStore
    Step7 --> |Update Status| StatusStore
    
    StatusStore --> StatusAPI
    StatusAPI --> |JSON Response| StatusUI[📊 Status UI<br/>Progress Bar<br/>Step indicators]
    
    %% Polling Loop
    StatusUI --> |Poll every 2s| StatusAPI
    
    %% Final Output
    Step7 --> |Success| FinalVideo[🎬 outputs/{run_id}/ad_final.mp4]
    Step7 --> |Failure| ErrorState[💥 Error State]
    
    FinalVideo --> DownloadAPI
    DownloadAPI --> |FileResponse| VideoDownload[⬇️ Download Video<br/>Browser saves file]
    
    %% Storage
    SaveFiles --> UploadsDir[(📂 uploads/{run_id}/<br/>- image1.jpg<br/>- logo.png<br/>- audio.wav<br/>- brief.txt)]
    FinalVideo --> OutputsDir[(📂 outputs/{run_id}/<br/>- ad_final.mp4)]
    
    %% Error Handling
    Reject --> ErrorUI[❌ Upload Error UI]
    ParamError --> ErrorUI
    ErrorState --> ErrorUI
    
    %% Styling
    classDef frontend fill:#e1f5fe
    classDef api fill:#f3e5f5
    classDef pipeline fill:#e8f5e8
    classDef storage fill:#fff3e0
    classDef error fill:#ffebee
    
    class UploadForm,RunButton,StatusUI frontend
    class UploadAPI,RunAPI,StatusAPI,DownloadAPI api
    class Pipeline,Step1,Step2,Step3,Step4,Step5,Step6,Step7 pipeline
    class UploadsDir,OutputsDir,StatusStore storage
    class Reject,ParamError,ErrorState,ErrorUI error
```

## Flow Description

### Frontend Layer (Blue)
- **UploadForm Component**: Handles drag-and-drop file uploads with validation
- **RunAgentButton Component**: Manages pipeline configuration and status monitoring
- **Status UI**: Real-time progress tracking with polling every 2 seconds

### API Layer (Purple)
- **Upload Handler**: File validation, storage, and run_id generation
- **Run Handler**: Parameter validation and background task queuing
- **Status Handler**: Real-time pipeline status updates
- **Download Handler**: Final video file delivery

### Pipeline Layer (Green)
7-step AI-powered ad creation process using CrewAI agents:
1. **CURATE**: Asset categorization and organization
2. **SCRIPT**: Ad copy generation based on tone and length
3. **DIRECT**: Storyboard and shot sequence creation
4. **NARRATE**: Voice synthesis using Kokoro TTS
5. **MUSIC**: Background audio supervision
6. **EDIT**: Video composition using MoviePy and ffmpeg
7. **QA**: Quality assurance and validation

### Storage Layer (Orange)
- **uploads/{run_id}/**: User-provided assets (images, audio, text)
- **outputs/{run_id}/**: Generated video files
- **In-Memory Status Store**: Thread-safe pipeline status tracking

### Error Handling (Red)
- File type validation
- Parameter validation  
- Pipeline failure recovery
- User error messaging

## Key Features

- **Asynchronous Processing**: Long-running AI pipeline executes in background
- **Real-time Updates**: Frontend polls status every 2 seconds
- **Multi-agent AI**: Specialized CrewAI agents for each pipeline step
- **Thread-safe Status**: Concurrent access to pipeline status
- **Graceful Error Handling**: Validation and recovery at multiple stages
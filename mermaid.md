# CrewAd Flow Diagram (Legacy)

**Note: This content has been merged into the main README.md file. Please refer to README.md for the most up-to-date documentation.**

This Mermaid diagram illustrates the complete user journey from file upload to video download in the CrewAd AI-native ad studio.

```mermaid
graph TD
    %% User Actions
    User[User] --> Upload[Upload Files]
    Upload --> Config[Configure Parameters]
    
    %% Frontend Components
    Upload --> UploadForm[UploadForm Component]
    Config --> RunButton[RunAgentButton Component]
    
    %% API Endpoints
    UploadForm --> |POST /api/upload| UploadAPI[Upload Handler]
    RunButton --> |POST /api/run| RunAPI[Run Handler]
    RunButton --> |GET /api/status| StatusAPI[Status Handler]
    RunButton --> |GET /api/download| DownloadAPI[Download Handler]
    
    %% Backend Processing
    UploadAPI --> FileValidation[Validate Files]
    FileValidation --> |Valid| SaveFiles[Save to uploads/run_id/]
    FileValidation --> |Invalid| Reject[Reject Files]
    SaveFiles --> ReturnRunID[Return run_id]
    
    RunAPI --> ValidateParams[Validate Parameters]
    ValidateParams --> |Valid| BackgroundTask[Queue Background Task]
    ValidateParams --> |Invalid| ParamError[Parameter Error]
    
    %% CrewAI Pipeline
    BackgroundTask --> Pipeline[AdCreationPipeline]
    
    Pipeline --> Step1[1. CURATE - AssetCuratorAgent]
    Step1 --> Step2[2. SCRIPT - ScriptwrightAgent]
    Step2 --> Step3[3. DIRECT - DirectorAgent]
    Step3 --> Step4[4. NARRATE - NarratorAgent]
    Step4 --> Step5[5. MUSIC - MusicSupervisorAgent]
    Step5 --> Step6[6. EDIT - EditorAgent]
    Step6 --> Step7[7. QA - QAAgent]
    
    %% Status Updates
    Step1 --> StatusStore[In-Memory Status Store]
    Step2 --> StatusStore
    Step3 --> StatusStore
    Step4 --> StatusStore
    Step5 --> StatusStore
    Step6 --> StatusStore
    Step7 --> StatusStore
    
    StatusStore --> StatusAPI
    StatusAPI --> StatusUI[Status UI with Progress Bar]
    
    %% Polling Loop
    StatusUI --> |Poll every 2s| StatusAPI
    
    %% Final Output
    Step7 --> |Success| FinalVideo[outputs/run_id/ad_final.mp4]
    Step7 --> |Failure| ErrorState[Error State]
    
    FinalVideo --> DownloadAPI
    DownloadAPI --> VideoDownload[Download Video]
    
    %% Storage
    SaveFiles --> UploadsDir[uploads/run_id/files]
    FinalVideo --> OutputsDir[outputs/run_id/video]
    
    %% Error Handling
    Reject --> ErrorUI[Upload Error UI]
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
- **UploadForm Component**: Handles single/multiple file uploads with auto-categorization
- **RunAgentButton Component**: Manages pipeline configuration and real-time status monitoring
- **Status UI**: Real-time progress tracking with 2-second polling intervals

### API Layer (Purple)
- **Upload Handler**: File validation, categorization, and run_id generation
- **Run Handler**: Parameter validation and background task queuing
- **Status Handler**: Thread-safe pipeline status updates
- **Download Handler**: Final MP4 video delivery

### Pipeline Layer (Green)
7-stage AI-powered ad creation using specialized CrewAI agents:
1. **CURATE**: Asset validation, categorization, and organization
2. **SCRIPT**: RAG-enhanced ad copy generation based on tone/length parameters
3. **DIRECT**: Intelligent storyboard creation with Ken Burns motion planning
4. **NARRATE**: Voice synthesis using Kokoro TTS with espeak-ng fallback
5. **MUSIC**: Background audio supervision (MVP placeholder)
6. **EDIT**: Professional video composition using MoviePy and ffmpeg
7. **QA**: Output validation and metadata generation

### Storage Layer (Orange)
- **uploads/{run_id}/**: User-provided assets (images, logos, audio, briefs)
- **outputs/{run_id}/**: Generated videos with metadata
- **In-Memory Status Store**: Thread-safe concurrent pipeline status tracking

### Error Handling (Red)
- File type validation
- Parameter validation  
- Pipeline failure recovery
- User error messaging

## Key Technical Features

- **Asynchronous Processing**: Long-running AI pipeline executes in FastAPI background tasks
- **Real-time Status Updates**: Frontend polls pipeline status every 2 seconds
- **Multi-agent AI Architecture**: Specialized CrewAI agents for each processing stage
- **Thread-safe Concurrent Access**: Safe pipeline status tracking across requests
- **Comprehensive Error Handling**: Validation and graceful failure recovery at all stages
- **Single/Multiple File Support**: Upload individual files or batches with auto-categorization
- **Python 3.11 Compatibility**: Optimized for stable package versions and ChromaDB integration
- **Professional Video Output**: Ken Burns effects, proper audio mixing, and MP4 optimization
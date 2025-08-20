const { useState, useEffect } = React;

function UploadForm({ onUploaded }) {
    const [files, setFiles] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [dragOver, setDragOver] = useState(false);
    const [error, setError] = useState('');

    const handleDrop = (e) => {
        e.preventDefault();
        setDragOver(false);
        const droppedFiles = Array.from(e.dataTransfer.files);
        setFiles(prev => [...prev, ...droppedFiles]);
    };

    const handleFileInput = (e) => {
        const selectedFiles = Array.from(e.target.files);
        setFiles(prev => [...prev, ...selectedFiles]);
    };

    const removeFile = (index) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
    };

    const uploadFiles = async () => {
        if (files.length === 0) {
            setError('Please select files to upload');
            return;
        }

        setUploading(true);
        setError('');

        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.status}`);
            }

            const result = await response.json();
            console.log('Upload result:', result);
            onUploaded(result.run_id);
        } catch (err) {
            console.error('Upload error:', err);
            setError(err.message);
        } finally {
            setUploading(false);
        }
    };

    const formatFileSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    return (
        <div className="step active">
            <div className="step-header">
                <div className="step-number">1</div>
                <div className="step-title">Upload Your Assets</div>
            </div>
            
            <div 
                className={`file-drop-zone ${dragOver ? 'dragover' : ''} ${files.length > 0 ? 'has-files' : ''}`}
                onDrop={handleDrop}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onClick={() => document.getElementById('file-input').click()}
            >
                <div className="drop-zone-text">
                    {files.length > 0 ? `${files.length} files selected` : 'Drop files here or click to browse'}
                </div>
                <div className="drop-zone-subtext">
                    Support: Images (JPG, PNG, WebP), Audio (WAV, MP3), Text files (TXT, MD)
                </div>
                <input
                    id="file-input"
                    type="file"
                    multiple
                    style={{ display: 'none' }}
                    onChange={handleFileInput}
                    accept=".jpg,.jpeg,.png,.webp,.gif,.wav,.mp3,.m4a,.txt,.md"
                />
            </div>

            {files.length > 0 && (
                <div className="file-list">
                    {files.map((file, index) => (
                        <div key={index} className="file-item">
                            <span className="file-name">{file.name}</span>
                            <span className="file-size">{formatFileSize(file.size)}</span>
                            <button 
                                onClick={(e) => { e.stopPropagation(); removeFile(index); }}
                                style={{ marginLeft: '10px', background: 'none', border: 'none', cursor: 'pointer', color: '#999' }}
                            >
                                ×
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {error && <div className="error-message">{error}</div>}

            <div style={{ marginTop: '20px' }}>
                <button 
                    className="btn"
                    onClick={uploadFiles}
                    disabled={uploading || files.length === 0}
                >
                    {uploading ? 'Uploading...' : 'Upload Files'}
                </button>
            </div>
        </div>
    );
}

function RunAgentButton({ runId }) {
    const [isRunning, setIsRunning] = useState(false);
    const [status, setStatus] = useState(null);
    const [error, setError] = useState('');
    const [parameters, setParameters] = useState({
        target_length: 30,
        tone: 'confident',
        voice: 'default',
        aspect: '16:9'
    });

    const startPipeline = async () => {
        setIsRunning(true);
        setError('');

        const formData = new FormData();
        Object.entries(parameters).forEach(([key, value]) => {
            formData.append(key, value);
        });
        formData.append('run_id', runId);

        try {
            const response = await fetch('/api/run', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`Failed to start pipeline: ${response.status}`);
            }

            const result = await response.json();
            console.log('Pipeline started:', result);
            
            // Start polling for status
            pollStatus();
        } catch (err) {
            console.error('Pipeline error:', err);
            setError(err.message);
            setIsRunning(false);
        }
    };

    const pollStatus = async () => {
        try {
            const response = await fetch(`/api/status/${runId}`);
            if (response.ok) {
                const statusData = await response.json();
                setStatus(statusData);
                
                // Continue polling if still running
                if (statusData.overall_status === 'running') {
                    setTimeout(pollStatus, 2000);
                } else {
                    setIsRunning(false);
                }
            }
        } catch (err) {
            console.error('Status polling error:', err);
        }
    };

    const downloadVideo = async () => {
        try {
            const response = await fetch(`/api/download/${runId}`);
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `ad_${runId}.mp4`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                throw new Error('Video not ready for download');
            }
        } catch (err) {
            console.error('Download error:', err);
            setError(err.message);
        }
    };

    const getStepStatus = (stepName) => {
        if (!status || !status.steps) return 'pending';
        
        const step = status.steps.find(s => s.step === stepName);
        if (!step) return 'pending';
        
        if (step.status === 'running') return 'running';
        if (step.status === 'completed') return 'completed';
        if (step.status === 'failed') return 'failed';
        return 'pending';
    };

    const calculateProgress = () => {
        if (!status || !status.steps) return 0;
        
        const totalSteps = 7; // curate, script, direct, narrate, music, edit, qa
        const completedSteps = status.steps.filter(s => s.status === 'completed').length;
        return (completedSteps / totalSteps) * 100;
    };

    const stepLabels = {
        curate: 'Asset Curation',
        script: 'Script Generation', 
        direct: 'Storyboard Creation',
        narrate: 'Voice Synthesis',
        music: 'Music Supervision',
        edit: 'Video Rendering',
        qa: 'Quality Assurance'
    };

    return (
        <div className="step active">
            <div className="step-header">
                <div className="step-number">2</div>
                <div className="step-title">Configure & Generate Ad</div>
            </div>

            <div className="form-row">
                <div className="form-group">
                    <label className="form-label">Target Length (seconds)</label>
                    <input
                        type="number"
                        className="form-input"
                        value={parameters.target_length}
                        onChange={(e) => setParameters(prev => ({ ...prev, target_length: parseInt(e.target.value) }))}
                        min="5"
                        max="120"
                        disabled={isRunning}
                    />
                </div>

                <div className="form-group">
                    <label className="form-label">Tone</label>
                    <select
                        className="form-select"
                        value={parameters.tone}
                        onChange={(e) => setParameters(prev => ({ ...prev, tone: e.target.value }))}
                        disabled={isRunning}
                    >
                        <option value="confident">Confident</option>
                        <option value="friendly">Friendly</option>
                        <option value="professional">Professional</option>
                        <option value="casual">Casual</option>
                        <option value="urgent">Urgent</option>
                        <option value="calm">Calm</option>
                    </select>
                </div>

                <div className="form-group">
                    <label className="form-label">Aspect Ratio</label>
                    <select
                        className="form-select"
                        value={parameters.aspect}
                        onChange={(e) => setParameters(prev => ({ ...prev, aspect: e.target.value }))}
                        disabled={isRunning}
                    >
                        <option value="16:9">16:9 (Landscape)</option>
                        <option value="9:16">9:16 (Portrait)</option>
                        <option value="1:1">1:1 (Square)</option>
                    </select>
                </div>
            </div>

            {error && <div className="error-message">{error}</div>}

            <div style={{ marginTop: '20px' }}>
                <button 
                    className="btn"
                    onClick={startPipeline}
                    disabled={isRunning}
                >
                    {isRunning ? 'Generating Ad...' : 'Generate Ad'}
                </button>
            </div>

            {status && (
                <div className="status-panel">
                    <h3 style={{ marginBottom: '15px' }}>Pipeline Status</h3>
                    
                    <div className="progress-bar">
                        <div 
                            className="progress-fill"
                            style={{ width: `${calculateProgress()}%` }}
                        ></div>
                    </div>

                    {Object.entries(stepLabels).map(([step, label]) => (
                        <div key={step} className="status-item">
                            <div className={`status-icon ${getStepStatus(step)}`}></div>
                            <span>{label}</span>
                            {status.steps && status.steps.find(s => s.step === step)?.extra && (
                                <span style={{ marginLeft: 'auto', fontSize: '0.9em', color: '#666' }}>
                                    {JSON.stringify(status.steps.find(s => s.step === step).extra)}
                                </span>
                            )}
                        </div>
                    ))}

                    {status.overall_status === 'success' && (
                        <div style={{ marginTop: '20px', textAlign: 'center' }}>
                            <div className="success-message">
                                🎉 Your ad has been generated successfully!
                            </div>
                            <button 
                                className="btn btn-success"
                                onClick={downloadVideo}
                            >
                                Download Video
                            </button>
                        </div>
                    )}

                    {status.overall_status === 'failed' && (
                        <div className="error-message">
                            ❌ Pipeline failed. Please check the logs and try again.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

function App() {
    const [runId, setRunId] = useState(null);

    return (
        <>
            <UploadForm onUploaded={setRunId} />
            {runId && <RunAgentButton runId={runId} />}
        </>
    );
}

import React, { useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

/* ----------------------- Upload ----------------------- */
function UploadForm({ onUploaded }) {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFiles = Array.from(e.dataTransfer.files || []);
    setFiles((prev) => [...prev, ...droppedFiles]);
  };

  const handleFileInput = (e) => {
    const selected = Array.from(e.target.files || []);
    setFiles((prev) => [...prev, ...selected]);
  };

  const removeFile = (index) => setFiles((prev) => prev.filter((_, i) => i !== index));

  const uploadFiles = async () => {
    if (!files.length) {
      setError("Please select files to upload");
      return;
    }
    setUploading(true);
    setError("");

    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));

    try {
      const res = await fetch(`${API}/upload`, { method: "POST", body: formData });
      if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
      const json = await res.json();
      onUploaded(json.run_id);
    } catch (err) {
      console.error(err);
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  return (
    <div className="step active">
      <div className="step-header">
        <div className="step-number">1</div>
        <div className="step-title">Upload Your Assets</div>
      </div>

      <div
        className={`file-drop-zone ${dragOver ? "dragover" : ""} ${files.length ? "has-files" : ""}`}
        onDrop={handleDrop}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onClick={() => document.getElementById("file-input").click()}
      >
        <div className="drop-zone-text">
          {files.length ? `${files.length} file${files.length > 1 ? "s" : ""} selected` : "Drop files here or click to browse"}
        </div>
        <div className="drop-zone-subtext">
          Upload images, logos, audio, or text briefs (one or more files)
          <br />
          Support: Images (JPG, PNG, WebP), Audio (WAV, MP3), Text files (TXT, MD)
        </div>
        <input
          id="file-input"
          type="file"
          multiple
          style={{ display: "none" }}
          onChange={handleFileInput}
          accept=".jpg,.jpeg,.png,.webp,.gif,.wav,.mp3,.m4a,.txt,.md"
        />
      </div>

      {files.length > 0 && (
        <div className="file-list">
          {files.map((file, i) => (
            <div key={`${file.name}-${i}`} className="file-item">
              <span className="file-name">{file.name}</span>
              <span className="file-size">{formatFileSize(file.size)}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(i);
                }}
                style={{ marginLeft: 10, background: "none", border: "none", cursor: "pointer", color: "#999" }}
                aria-label={`Remove ${file.name}`}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      <div style={{ marginTop: 20 }}>
        <button className="btn" onClick={uploadFiles} disabled={uploading || !files.length}>
          {uploading ? "Uploading..." : files.length === 1 ? "Upload File" : "Upload Files"}
        </button>
      </div>
    </div>
  );
}

/* ----------------------- Run / Status ----------------------- */
function RunAgentButton({ runId }) {
  const [isRunning, setIsRunning] = useState(false);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");
  const [parameters, setParameters] = useState({
    target_length: 30,
    tone: "confident",
    voice: "mute",       // <— default to mute so the run can complete while TTS is being tuned
    aspect: "16:9",
  });

  const startPipeline = async () => {
    setIsRunning(true);
    setError("");

    try {
      // Send JSON to /run (your backend accepts JSON here)
      const res = await fetch(`${API}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          run_id: runId,
          target_length: parameters.target_length,
          tone: parameters.tone,
          voice: parameters.voice,
          aspect: parameters.aspect,
        }),
      });
      if (!res.ok) throw new Error(`Failed to start pipeline: ${res.status}`);
      pollStatus();
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to start pipeline");
      setIsRunning(false);
    }
  };

  const pollStatus = async () => {
    try {
      const res = await fetch(`${API}/status/${runId}`);
      if (res.ok) {
        const json = await res.json();
        setStatus(json);
        const overall = (json?.overall_status || "").toLowerCase();
        if (overall === "running" || overall === "started") {
          setTimeout(pollStatus, 2000);
        } else {
          setIsRunning(false);
        }
      } else {
        setTimeout(pollStatus, 2500);
      }
    } catch (err) {
      console.error("Status polling error:", err);
      setTimeout(pollStatus, 2500);
    }
  };

  const downloadVideo = async () => {
    try {
      const res = await fetch(`${API}/download/${runId}`);
      if (!res.ok) throw new Error("Video not ready for download");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ad_${runId}.mp4`;
      document.body.appendChild(a);
      a.click();
      URL.revokeObjectURL(url);
      a.remove();
    } catch (err) {
      console.error("Download error:", err);
      setError(err.message || "Download failed");
    }
  };

  const getStepStatus = (stepName) => {
    if (!status?.steps) return "pending";
    const step = status.steps.find((s) => s.step === stepName);
    if (!step) return "pending";
    if (step.status === "running") return "running";
    if (step.status === "completed") return "completed";
    if (step.status === "failed") return "failed";
    return "pending";
  };

  const calculateProgress = () => {
    if (!status?.steps) return 0;
    const total = 7; // curate, script, direct, narrate, music, edit, qa
    const done = status.steps.filter((s) => s.status === "completed").length;
    return (done / total) * 100;
  };

  const stepLabels = {
    curate: "Asset Curation",
    script: "Script Generation",
    direct: "Storyboard Creation",
    narrate: "Voice Synthesis",
    music: "Music Supervision",
    edit: "Video Rendering",
    qa: "Quality Assurance",
  };

  const overall = (status?.overall_status || "").toLowerCase();
  const finished = overall === "done" || overall === "success";

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
            onChange={(e) =>
              setParameters((p) => ({
                ...p,
                target_length: Math.max(0, parseInt(e.target.value || "0", 10)),
              }))
            }
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
            onChange={(e) => setParameters((p) => ({ ...p, tone: e.target.value }))}
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
            onChange={(e) => setParameters((p) => ({ ...p, aspect: e.target.value }))}
            disabled={isRunning}
          >
            <option value="16:9">16:9 (Landscape)</option>
            <option value="9:16">9:16 (Portrait)</option>
            <option value="1:1">1:1 (Square)</option>
          </select>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div style={{ marginTop: 20 }}>
        <button className="btn" onClick={startPipeline} disabled={isRunning}>
          {isRunning ? "Generating Ad..." : "Generate Ad"}
        </button>
      </div>

      {status && (
        <div className="status-panel">
          <h3 style={{ marginBottom: 15 }}>Pipeline Status</h3>

          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${calculateProgress()}%` }} />
          </div>

          {Object.entries(stepLabels).map(([step, label]) => (
            <div key={step} className="status-item">
              <div className={`status-icon ${getStepStatus(step)}`} />
              <span>{label}</span>
              {status.steps?.find((s) => s.step === step)?.extra && (
                <span style={{ marginLeft: "auto", fontSize: ".9em", color: "#666" }}>
                  {JSON.stringify(status.steps.find((s) => s.step === step).extra)}
                </span>
              )}
            </div>
          ))}

          {finished && (
            <div style={{ marginTop: 20, textAlign: "center" }}>
              <div className="success-message">🎉 Your ad has been generated successfully!</div>
              <button className="btn btn-success" onClick={downloadVideo}>
                Download Video
              </button>
            </div>
          )}

          {overall === "failed" && (
            <div className="error-message">❌ Pipeline failed. Please check the logs and try again.</div>
          )}
        </div>
      )}
    </div>
  );
}

/* ----------------------- App ----------------------- */
export default function App() {
  const [runId, setRunId] = useState(null);
  return (
    <>
      <UploadForm onUploaded={setRunId} />
      {runId && <RunAgentButton runId={runId} />}
    </>
  );
}

import React, { useEffect, useState } from "react";

export default function RunAgentButton({ runId }) {
  const [status, setStatus] = useState([]);
  const [running, setRunning] = useState(false);

  const start = async () => {
    setRunning(true);
    const fd = new FormData();
    fd.append("run_id", runId);
    fd.append("target_length", 30);
    fd.append("tone", "confident");
    fd.append("voice", "af_heart");
    fd.append("aspect", "16:9");
    await fetch("/api/run", { method: "POST", body: fd });
  };

  useEffect(() => {
    if (!running) return;
    const id = setInterval(async () => {
      const r = await fetch(`/api/status/${runId}`);
      const d = await r.json();
      setStatus(d.steps || []);
    }, 1500);
    return () => clearInterval(id);
  }, [running, runId]);

  return (
    <div style={{ border: "1px solid #ddd", padding: 12, marginTop: 12 }}>
      <h4>2) Generate Ad</h4>
      <button onClick={start} disabled={running}>Run Crew</button>
      <div style={{ marginTop: 12 }}>
        {status.map((s, i) => (
          <div key={i}>
            <b>{s.step}</b>: {s.status} {s.extra ? JSON.stringify(s.extra) : ""}
          </div>
        ))}
      </div>
      <div style={{ marginTop: 12 }}>
        <a href={`/api/download/${runId}`} target="_blank" rel="noreferrer">Download (when ready)</a>
      </div>
    </div>
  );
}

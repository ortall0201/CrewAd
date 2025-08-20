import React, { useState } from "react";

export default function UploadForm({ onUploaded }) {
  const [files, setFiles] = useState([]);

  const submit = async () => {
    const fd = new FormData();
    files.forEach(f => fd.append("files", f));
    const r = await fetch("/api/upload", { method: "POST", body: fd });
    const data = await r.json();
    onUploaded(data.run_id);
  };

  return (
    <div style={{ border: "1px solid #ddd", padding: 12, marginTop: 12 }}>
      <h4>1) Upload assets</h4>
      <input multiple type="file" onChange={(e)=>setFiles([...e.target.files])}/>
      <button onClick={submit} disabled={!files.length} style={{ marginLeft: 8 }}>
        Upload
      </button>
    </div>
  );
}

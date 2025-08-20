import React, { useState } from "react";
import UploadForm from "./components/UploadForm.js";
import RunAgentButton from "./components/RunAgentButton.js";

export default function App() {
  const [runId, setRunId] = useState(null);
  return (
    <div style={{ fontFamily: "sans-serif", padding: 20 }}>
      <h2>Folder-in, Ad-out</h2>
      <UploadForm onUploaded={setRunId} />
      {runId && <RunAgentButton runId={runId} />}
    </div>
  );
}

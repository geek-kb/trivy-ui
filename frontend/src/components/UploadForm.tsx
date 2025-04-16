import {useState} from "react";

export default function UploadForm({
  onUploadSuccess,
}: {
  onUploadSuccess?: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState("");

  const handleUpload = async () => {
    if (!file) {
      setStatus("❌ No file selected");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/upload-report", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const error = await res.text();
        setStatus(`❌ Upload failed: ${error}`);
        return;
      }

      const data = await res.json();
      console.log("Upload response:", data);

      if (!data.id) {
        setStatus("❌ Upload succeeded but response is missing 'id'");
      } else {
        setStatus(`✅ Uploaded! Report ID: ${data.id}`);
        if (onUploadSuccess) onUploadSuccess(); // <-- trigger parent reload
      }
    } catch (err: any) {
      console.error("Upload error:", err);
      setStatus(`❌ Upload error: ${err.message}`);
    }
  };

  return (
    <div style={{marginBottom: "2rem"}}>
      <input
        type="file"
        accept=".json"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <button onClick={handleUpload} style={{marginLeft: "0.5rem"}}>
        Upload
      </button>
      {status && <p>{status}</p>}
    </div>
  );
}

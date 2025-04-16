import {useState} from "react";

export default function UploadForm({
  onUploadSuccess,
}: {
  onUploadSuccess?: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<
    "idle" | "uploading" | "success" | "error"
  >("idle");
  const [message, setMessage] = useState("");

  const handleUpload = async () => {
    if (!file) {
      setStatus("error");
      setMessage("No file selected");
      return;
    }

    setStatus("uploading");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/upload-report", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errorText = await res.text();
        setStatus("error");
        setMessage(`Upload failed: ${errorText}`);
        return;
      }

      const data = await res.json();
      if (!data.id) {
        setStatus("error");
        setMessage("Upload succeeded but no ID in response");
      } else {
        setStatus("success");
        setMessage(`Uploaded! Report ID: ${data.id}`);
        onUploadSuccess?.();
      }
    } catch (err: any) {
      setStatus("error");
      setMessage(`Upload error: ${err.message}`);
    }
  };

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
      <input
        type="file"
        accept=".json"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
        className="text-sm"
      />
      <button
        onClick={handleUpload}
        className="px-4 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
      >
        Upload
      </button>
      {status !== "idle" && (
        <p
          className={`text-sm ${
            status === "success"
              ? "text-green-500"
              : status === "error"
                ? "text-red-500"
                : "text-gray-400"
          }`}
        >
          {message}
        </p>
      )}
    </div>
  );
}

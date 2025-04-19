import {useState, useRef, useEffect, useCallback} from "react";
import {toast, Toaster} from "react-hot-toast";

const allowedExtensions = [".json", ".spdx.json", ".cdx.json", ".tar"];
const allowedMimeTypes = [
  "application/json",
  "application/x-tar",
  "application/vnd.cyclonedx+json",
  "application/spdx+json",
];
const MAX_FILE_SIZE = 5 * 1024 * 1024;

function isValidFile(file: File) {
  const name = file.name.toLowerCase();
  return (
    allowedExtensions.some((ext) => name.endsWith(ext)) &&
    (allowedMimeTypes.includes(file.type) || file.type === "")
  );
}

export default function UploadForm({
  onUploadSuccess,
}: {
  onUploadSuccess?: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<"idle" | "validating" | "uploading">(
    "idle",
  );
  const inputRef = useRef<HTMLInputElement>(null);

  // <-- single toast when file changes
  useEffect(() => {
    if (file) {
      toast.success(`✅ Selected: ${file.name}`);
    }
  }, [file]);

  const processFile = (f: File) => {
    if (!isValidFile(f)) {
      toast.error("❌ Invalid file type.");
      return;
    }
    if (f.size > MAX_FILE_SIZE) {
      toast.error("❌ File too large (max 5MB).");
      return;
    }
    setFile(f);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) processFile(f);
  };

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) {
      if (inputRef.current) inputRef.current.value = ""; // avoid duplicate onChange
      processFile(f);
    }
  }, []);

  const handleUpload = async () => {
    if (!file) {
      toast.error("❌ Please select a file first.");
      return;
    }
    setStatus("validating");
    try {
      if (file.name.endsWith(".json")) {
        JSON.parse(await file.text());
      }
    } catch {
      setStatus("idle");
      toast.error("❌ Invalid JSON content.");
      return;
    }
    setStatus("uploading");
    const form = new FormData();
    form.append("file", file);
    const tid = toast.loading("Uploading...");
    try {
      const res = await fetch("/api/upload-report", {
        method: "POST",
        body: form,
      });
      toast.dismiss(tid);
      if (!res.ok) {
        const err = await res.text();
        setStatus("idle");
        toast.error(`❌ Upload failed: ${err}`);
        return;
      }
      const data = await res.json();
      if (!data.id) {
        setStatus("idle");
        toast.error("❌ No ID returned.");
      } else {
        toast.success("✅ Upload successful!");
        onUploadSuccess
          ? onUploadSuccess()
          : setTimeout(() => window.location.reload(), 1500);
      }
    } catch (e: any) {
      toast.dismiss(tid);
      setStatus("idle");
      toast.error(`❌ Upload error: ${e.message}`);
    }
  };

  return (
    <>
      <Toaster position="top-right" />
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        className="relative border-2 border-dashed p-8 rounded"
      >
        <input
          ref={inputRef}
          type="file"
          accept={allowedExtensions.join(",")}
          onChange={handleFileChange}
          className="hidden"
          id="file-upload"
        />
        <label htmlFor="file-upload" className="cursor-pointer">
          {file ? `Selected: ${file.name}` : "Click or drop a file to upload"}
        </label>
      </div>
      <button
        onClick={handleUpload}
        disabled={!file || status !== "idle"}
        className="mt-4 px-6 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
      >
        {status === "uploading" ? "Uploading…" : "Upload"}
      </button>
      {file && (
        <button
          onClick={() => {
            setFile(null);
            setStatus("idle");
            if (inputRef.current) inputRef.current.value = "";
          }}
          className="ml-4 underline text-sm"
        >
          Clear
        </button>
      )}
    </>
  );
}

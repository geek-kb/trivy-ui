// frontend/src/components/UploadForm.tsx
import {useState, useCallback} from "react";
import {toast, Toaster} from "react-hot-toast";

const allowedExtensions = [".json", ".spdx.json", ".cdx.json", ".tar"];
const allowedMimeTypes = [
  "application/json",
  "application/x-tar",
  "application/vnd.cyclonedx+json",
  "application/spdx+json",
];

// Max file size 5MB
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

function isValidFile(file: File) {
  const filename = file.name.toLowerCase();
  const extensionAllowed = allowedExtensions.some((ext) =>
    filename.endsWith(ext),
  );
  const mimeAllowed = allowedMimeTypes.includes(file.type) || file.type === "";
  return extensionAllowed && mimeAllowed;
}

export default function UploadForm({
  onUploadSuccess,
}: {
  onUploadSuccess?: () => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [status, setStatus] = useState<"idle" | "validating" | "uploading">(
    "idle",
  );

  const handleUpload = async () => {
    if (!file) {
      toast.error("Please select a file first.");
      return;
    }

    if (!isValidFile(file)) {
      toast.error(
        "Invalid file type. Only .json, .spdx.json, .cdx.json, or .tar files are allowed.",
      );
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      toast.error("File too large. Max allowed size is 5MB.");
      return;
    }

    setStatus("validating");
    try {
      if (
        file.name.endsWith(".json") ||
        file.name.endsWith(".spdx.json") ||
        file.name.endsWith(".cdx.json")
      ) {
        const text = await file.text();
        JSON.parse(text); // Validate JSON content
      }
    } catch (err) {
      setStatus("idle");
      toast.error(
        "Invalid JSON content. Please export the report with --format json.",
      );
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
        setStatus("idle");
        toast.error(`Upload failed: ${errorText}`);
        return;
      }

      const data = await res.json();
      if (!data.id) {
        setStatus("idle");
        toast.error("Upload succeeded but no ID returned.");
      } else {
        toast.success("Upload successful!");
        if (onUploadSuccess) {
          onUploadSuccess();
        } else {
          setTimeout(() => window.location.reload(), 1500);
        }
      }
    } catch (err: any) {
      setStatus("idle");
      toast.error(`Upload error: ${err.message}`);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragActive(false);
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles && droppedFiles.length > 0) {
      const droppedFile = droppedFiles[0];

      if (!isValidFile(droppedFile)) {
        toast.error("Invalid file type dropped.");
        return;
      }
      if (droppedFile.size > MAX_FILE_SIZE) {
        toast.error("Dropped file too large. Max allowed size is 5MB.");
        return;
      }
      setFile(droppedFile);
      toast.success(`Selected: ${droppedFile.name}`);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "copy";
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragActive(false);
  }, []);

  return (
    <>
      <Toaster position="top-right" />

      <div className="flex flex-col gap-4">
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative flex flex-col items-center justify-center border-2 border-dashed rounded-lg p-8 transition-colors ${
            dragActive
              ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
              : "border-gray-300 dark:border-gray-600"
          }`}
        >
          {dragActive && (
            <div className="absolute inset-0 flex items-center justify-center text-blue-600 dark:text-blue-300 font-semibold text-lg bg-white/80 dark:bg-gray-800/80 rounded-lg pointer-events-none">
              Drop your file here
            </div>
          )}

          {!dragActive && (
            <>
              <input
                type="file"
                accept={allowedExtensions.join(",")}
                onChange={(e) => {
                  const selectedFile = e.target.files?.[0] || null;
                  if (selectedFile) {
                    if (!isValidFile(selectedFile)) {
                      toast.error("Invalid file type selected.");
                      return;
                    }
                    if (selectedFile.size > MAX_FILE_SIZE) {
                      toast.error("Selected file too large. Max 5MB.");
                      return;
                    }
                    setFile(selectedFile);
                    toast.success(`Selected: ${selectedFile.name}`);
                  }
                  setStatus("idle");
                }}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="text-center cursor-pointer text-gray-500 dark:text-gray-300 text-sm hover:underline"
              >
                {file
                  ? `Selected: ${file.name}`
                  : "Click or drag a file to upload"}
              </label>
            </>
          )}
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={handleUpload}
            disabled={
              !file || status === "uploading" || status === "validating"
            }
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition disabled:opacity-50"
          >
            {status === "uploading" ? "Uploading..." : "Upload"}
          </button>

          {file && (
            <button
              onClick={() => {
                setFile(null);
                setStatus("idle");
                toast("Selection cleared", {icon: "🗑️"});
              }}
              className="text-sm text-gray-500 dark:text-gray-400 underline"
            >
              Clear selection
            </button>
          )}
        </div>
      </div>
    </>
  );
}

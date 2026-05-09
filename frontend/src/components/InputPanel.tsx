"use client";

import { useRef, useState } from "react";
import { FileText, Upload, X, CheckCircle, AlertCircle, Loader2 } from "lucide-react";

interface InputPanelProps {
  value: string;
  onChange: (value: string) => void;
  onDocumentUploaded?: (documentId: string, filename: string) => void;
}

type UploadStatus = "idle" | "uploading" | "success" | "error";

export default function InputPanel({ value, onChange, onDocumentUploaded }: InputPanelProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>("idle");
  const [uploadedFilename, setUploadedFilename] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Reset state
    setUploadStatus("uploading");
    setErrorMessage(null);
    setUploadedFilename(null);

    // For text/markdown files: preview content in textarea immediately
    if (file.type === "text/plain" || file.name.endsWith(".md") || file.name.endsWith(".txt")) {
      const reader = new FileReader();
      reader.onload = (ev) => {
        onChange(ev.target?.result as string ?? "");
      };
      reader.readAsText(file);
    } else {
      // For PDF: clear textarea and show filename indicator instead
      onChange("");
    }

    // Upload to backend
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("http://localhost:8000/api/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(errorData.detail ?? `HTTP ${response.status}`);
      }

      const data = await response.json();
      setUploadedFilename(file.name);
      setUploadStatus("success");
      onDocumentUploaded?.(data.document_id, file.name);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Upload failed";
      setErrorMessage(msg);
      setUploadStatus("error");
    } finally {
      // Reset the file input so the same file can be re-selected
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const clearFile = () => {
    setUploadStatus("idle");
    setUploadedFilename(null);
    setErrorMessage(null);
    onChange("");
    onDocumentUploaded?.("", "");
  };

  return (
    <>
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.md,.txt,.doc,.docx,text/plain,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        className="hidden"
        onChange={handleFileSelect}
        id="srs-file-input"
      />

      {/* Panel header */}
      <div className="p-4 border-b border-white/10 flex items-center justify-between bg-black/20">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-gray-400" />
          <h2 className="font-semibold">Raw Input (SRS)</h2>
        </div>

        <div className="flex items-center gap-2">
          {/* Upload status badge */}
          {uploadStatus === "uploading" && (
            <span className="flex items-center gap-1 px-2 py-1 text-xs rounded-md bg-blue-500/20 text-blue-300 border border-blue-500/30 animate-pulse">
              <Loader2 className="w-3 h-3 animate-spin" />
              Uploading…
            </span>
          )}
          {uploadStatus === "success" && uploadedFilename && (
            <span className="flex items-center gap-1 px-2 py-1 text-xs rounded-md bg-green-500/20 text-green-300 border border-green-500/30 max-w-[160px] truncate" title={uploadedFilename}>
              <CheckCircle className="w-3 h-3 flex-shrink-0" />
              {uploadedFilename}
            </span>
          )}
          {uploadStatus === "error" && (
            <span className="flex items-center gap-1 px-2 py-1 text-xs rounded-md bg-red-500/20 text-red-300 border border-red-500/30 max-w-[200px] truncate" title={errorMessage ?? "Error"}>
              <AlertCircle className="w-3 h-3 flex-shrink-0" />
              {errorMessage}
            </span>
          )}

          {/* Clear button (shown after upload) */}
          {(uploadStatus === "success" || uploadStatus === "error") && (
            <button
              onClick={clearFile}
              className="p-1 hover:bg-white/10 rounded-md transition-colors"
              title="Clear file"
            >
              <X className="w-3.5 h-3.5 text-gray-400" />
            </button>
          )}

          {/* Upload button */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadStatus === "uploading"}
            className="flex items-center gap-1.5 px-2.5 py-1.5 hover:bg-white/10 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed group"
            title="Upload SRS document (PDF, MD, TXT)"
          >
            <Upload className="w-4 h-4 text-gray-400 group-hover:text-blue-400 transition-colors" />
            <span className="text-xs text-gray-500 group-hover:text-blue-400 transition-colors hidden sm:inline">Upload</span>
          </button>
        </div>
      </div>

      {/* PDF / DOCX preview banner (when a binary doc is loaded) */}
      {uploadStatus === "success" &&
        uploadedFilename &&
        [".pdf", ".doc", ".docx"].some((ext) => uploadedFilename.endsWith(ext)) &&
        value === "" && (
        <div className="px-4 py-2 bg-blue-500/10 border-b border-blue-500/20 flex items-center gap-2">
          <FileText className="w-4 h-4 text-blue-400 flex-shrink-0" />
          <span className="text-xs text-blue-300">
            <strong>{uploadedFilename}</strong> uploaded — the backend will parse it directly. You can also add extra notes below.
          </span>
        </div>
      )}

      {/* Textarea */}
      <div className="flex-1 p-4 relative">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={
            uploadStatus === "success" &&
            uploadedFilename &&
            [".pdf", ".doc", ".docx"].some((ext) => uploadedFilename.endsWith(ext))
              ? `Optional: add extra context or notes for '${uploadedFilename}'…`
              : "Paste your Software Requirements Specification here…\n\nOr click Upload above to load a PDF, Word (.docx), Markdown, or Text file."
          }
          className="w-full h-full bg-transparent resize-none outline-none text-gray-300 placeholder-gray-600 focus:ring-0 leading-relaxed"
        />
        <div className="absolute bottom-4 right-4 text-xs text-gray-500 font-mono">
          {value.length} chars
        </div>
      </div>
    </>
  );
}

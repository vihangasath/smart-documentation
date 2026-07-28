"use client";

import { useRef, useState } from "react";
import { FileText, Upload, X, CheckCircle, AlertCircle, Loader2 } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

    setUploadStatus("uploading");
    setErrorMessage(null);
    setUploadedFilename(null);

    if (file.type === "text/plain" || file.name.endsWith(".md") || file.name.endsWith(".txt")) {
      const reader = new FileReader();
      reader.onload = (ev) => { onChange(ev.target?.result as string ?? ""); };
      reader.readAsText(file);
    } else {
      onChange("");
    }

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_URL}/api/upload`, {
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
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.md,.txt,.doc,.docx,text/plain,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        className="hidden"
        onChange={handleFileSelect}
        id="srs-file-input"
      />

      {/* Panel header */}
      <div
        className="px-4 py-3 border-b flex items-center justify-between"
        style={{ borderColor: "var(--border-color)", background: "var(--bg-card)" }}
      >
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4" style={{ color: "var(--text-muted)" }} />
          <h2 className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>
            SRS Input
          </h2>
        </div>

        <div className="flex items-center gap-1.5">
          {/* Status badges */}
          {uploadStatus === "uploading" && (
            <span className="flex items-center gap-1 px-2 py-0.5 text-xs rounded-md bg-blue-500/15 text-blue-500 border border-blue-500/20 animate-pulse">
              <Loader2 className="w-3 h-3 animate-spin" /> Uploading…
            </span>
          )}
          {uploadStatus === "success" && uploadedFilename && (
            <span
              className="flex items-center gap-1 px-2 py-0.5 text-xs rounded-md border max-w-[140px] truncate"
              style={{ background: "rgba(34,197,94,0.1)", color: "#22c55e", borderColor: "rgba(34,197,94,0.25)" }}
              title={uploadedFilename}
            >
              <CheckCircle className="w-3 h-3 flex-shrink-0" />
              {uploadedFilename}
            </span>
          )}
          {uploadStatus === "error" && (
            <span
              className="flex items-center gap-1 px-2 py-0.5 text-xs rounded-md border max-w-[180px] truncate"
              style={{ background: "rgba(239,68,68,0.1)", color: "#ef4444", borderColor: "rgba(239,68,68,0.25)" }}
              title={errorMessage ?? "Error"}
            >
              <AlertCircle className="w-3 h-3 flex-shrink-0" />
              {errorMessage}
            </span>
          )}

          {(uploadStatus === "success" || uploadStatus === "error") && (
            <button
              onClick={clearFile}
              className="p-1 rounded-md transition-colors hover:bg-[var(--bg-card-hover)]"
              title="Clear file"
            >
              <X className="w-3.5 h-3.5" style={{ color: "var(--text-muted)" }} />
            </button>
          )}

          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadStatus === "uploading"}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs transition-all
              disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              background: "var(--bg-card-hover)",
              border: "1px solid var(--border-color)",
              color: "var(--text-secondary)",
            }}
            title="Upload SRS document (PDF, MD, TXT)"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Upload</span>
          </button>
        </div>
      </div>

      {/* PDF / DOCX indicator */}
      {uploadStatus === "success" && uploadedFilename &&
        [".pdf", ".doc", ".docx"].some((ext) => uploadedFilename.endsWith(ext)) &&
        value === "" && (
        <div
          className="px-3 py-2 border-b flex items-center gap-2 text-xs"
          style={{
            background: "rgba(59,130,246,0.08)",
            borderColor: "rgba(59,130,246,0.2)",
            color: "#3b82f6",
          }}
        >
          <FileText className="w-3.5 h-3.5 flex-shrink-0" />
          <span>
            <strong>{uploadedFilename}</strong> — backend will parse it. Add extra notes below if needed.
          </span>
        </div>
      )}

      {/* Textarea */}
      <div className="flex-1 p-3 relative">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={
            uploadStatus === "success" && uploadedFilename &&
            [".pdf", ".doc", ".docx"].some((ext) => uploadedFilename.endsWith(ext))
              ? `Optional: add context for '${uploadedFilename}'…`
              : "Paste your SRS document here…\n\nOr click Upload to load a PDF, Word, Markdown, or TXT file."
          }
          className="w-full h-full bg-transparent resize-none outline-none leading-relaxed text-sm"
          style={{ color: "var(--text-primary)" }}
        />
        <div
          className="absolute bottom-3 right-3 text-[11px] font-mono"
          style={{ color: "var(--text-muted)" }}
        >
          {value.length} chars
        </div>
      </div>
    </>
  );
}

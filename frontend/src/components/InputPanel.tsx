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
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm hover:scale-[1.02] active:scale-95
              disabled:opacity-50 disabled:cursor-not-allowed bg-blue-600 hover:bg-blue-700 text-white"
            title="Upload SRS document (PDF, MD, TXT, DOCX)"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Document</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-4 relative flex flex-col">
        {uploadStatus === "success" && uploadedFilename && [".pdf", ".doc", ".docx"].some((ext) => uploadedFilename.endsWith(ext)) ? (
          <div className="flex-1 flex flex-col items-center justify-center p-6 border-2 border-dashed border-green-500/30 rounded-xl bg-green-500/5 mb-4 text-center">
            <div className="w-16 h-16 bg-green-500/10 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
            <h3 className="text-lg font-semibold text-green-600 dark:text-green-400 mb-1">
              Document Uploaded Successfully
            </h3>
            <p className="text-sm font-medium text-green-700 dark:text-green-300 mb-2 truncate max-w-full px-4">
              {uploadedFilename}
            </p>
            <p className="text-xs text-green-600/70 dark:text-green-400/70 max-w-sm">
              The backend will parse this document automatically. You can add additional context or notes in the text area below if needed.
            </p>
          </div>
        ) : value === "" && uploadStatus === "idle" ? (
          <div 
            onClick={() => fileInputRef.current?.click()}
            className="absolute inset-4 border-2 border-dashed rounded-xl flex flex-col items-center justify-center cursor-pointer transition-all hover:bg-blue-50/50 dark:hover:bg-blue-900/10 hover:border-blue-400"
            style={{ borderColor: "var(--border-color)", background: "var(--bg-card)" }}
          >
            <div className="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mb-3">
              <Upload className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 className="text-base font-medium mb-1" style={{ color: "var(--text-primary)" }}>
              Upload your SRS Document
            </h3>
            <p className="text-xs text-center max-w-[250px]" style={{ color: "var(--text-muted)" }}>
              Drag and drop is not yet supported. Click here or use the upload button above to select a PDF, Word, or Text file.
            </p>
          </div>
        ) : null}

        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={
            uploadStatus === "success" && uploadedFilename &&
            [".pdf", ".doc", ".docx"].some((ext) => uploadedFilename.endsWith(ext))
              ? `Optional: add context for '${uploadedFilename}'…`
              : "Paste your SRS document here…\n\nOr click Upload to load a PDF, Word, Markdown, or TXT file."
          }
          className={`w-full bg-transparent resize-none outline-none leading-relaxed text-sm ${
            (uploadStatus === "success" && uploadedFilename && [".pdf", ".doc", ".docx"].some((ext) => uploadedFilename.endsWith(ext))) ? "h-32 p-3 border rounded-lg" : "flex-1 absolute inset-4 p-4 z-10 bg-transparent"
          }`}
          style={{ 
            color: "var(--text-primary)",
            borderColor: "var(--border-color)",
            backgroundColor: (uploadStatus === "success" && uploadedFilename && [".pdf", ".doc", ".docx"].some((ext) => uploadedFilename.endsWith(ext))) ? "var(--bg-card-hover)" : "transparent"
          }}
        />
        
        {value.length > 0 && (
          <div
            className="absolute bottom-6 right-6 text-[11px] font-mono px-2 py-1 rounded bg-black/5 dark:bg-white/10 z-20"
            style={{ color: "var(--text-muted)" }}
          >
            {value.length} chars
          </div>
        )}
      </div>
    </>
  );
}

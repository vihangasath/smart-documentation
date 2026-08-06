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
        className="px-5 py-4 border-b flex items-center justify-between bg-[var(--bg-card)]"
        style={{ borderColor: "var(--border-color)" }}
      >
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-blue-500" />
          <h2 className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>
            Provide Requirements
          </h2>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Status badges for top right if needed, but we'll show them in the main area now */}
          {uploadStatus === "error" && (
            <span
              className="flex items-center gap-1 px-2 py-1 text-xs rounded-md border"
              style={{ background: "rgba(239,68,68,0.1)", color: "#ef4444", borderColor: "rgba(239,68,68,0.25)" }}
              title={errorMessage ?? "Error"}
            >
              <AlertCircle className="w-3 h-3" />
              {errorMessage}
            </span>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-5 flex flex-col gap-4 overflow-y-auto bg-[var(--bg-primary)] relative">
        
        {/* Upload Zone (The "Uploading Button") */}
        <div className="shrink-0 w-full">
          {uploadStatus === "success" && uploadedFilename && [".pdf", ".doc", ".docx"].some((ext) => uploadedFilename.endsWith(ext)) ? (
            <div className="relative flex items-center gap-4 p-4 border rounded-xl bg-green-500/10 border-green-500/30 transition-all shadow-sm">
              <div className="w-10 h-10 bg-green-500/20 rounded-full flex items-center justify-center shrink-0">
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold text-green-700 dark:text-green-400 mb-0.5 truncate">
                  {uploadedFilename}
                </h3>
                <p className="text-xs text-green-600/80 dark:text-green-400/80">
                  Document attached successfully. The backend will analyze it.
                </p>
              </div>
              <button
                onClick={clearFile}
                className="p-2 shrink-0 rounded-lg hover:bg-green-500/20 text-green-700 dark:text-green-400 transition-colors"
                title="Remove file"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div 
              onClick={() => {
                if (uploadStatus !== "uploading") fileInputRef.current?.click();
              }}
              className={`
                group relative flex flex-col items-center justify-center p-6 border-2 border-dashed rounded-xl cursor-pointer transition-all duration-200
                ${uploadStatus === "uploading" ? "opacity-70 cursor-wait bg-blue-50/50 dark:bg-blue-900/10 border-blue-400" : "hover:bg-blue-50/50 dark:hover:bg-blue-900/10 hover:border-blue-400 hover:shadow-sm"}
              `}
              style={{ 
                borderColor: uploadStatus === "uploading" ? "#60a5fa" : "var(--border-color)", 
                background: uploadStatus === "uploading" ? "" : "var(--bg-card)" 
              }}
            >
              <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-3 transition-colors ${uploadStatus === "uploading" ? "bg-blue-100 dark:bg-blue-900/40" : "bg-blue-50 dark:bg-blue-900/20 group-hover:bg-blue-100 dark:group-hover:bg-blue-900/40"}`}>
                {uploadStatus === "uploading" ? (
                  <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
                ) : (
                  <Upload className="w-6 h-6 text-blue-500" />
                )}
              </div>
              <h3 className="text-sm font-semibold mb-1" style={{ color: "var(--text-primary)" }}>
                {uploadStatus === "uploading" ? "Uploading Document..." : "Click to Upload SRS Document"}
              </h3>
              <p className="text-xs text-center max-w-[280px]" style={{ color: "var(--text-muted)" }}>
                Attach a PDF, Word, or Text file.
              </p>
            </div>
          )}
        </div>

        {/* Text Area Zone */}
        <div className="flex-1 flex flex-col relative rounded-xl border shadow-sm transition-all focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500/50"
          style={{ background: "var(--bg-card)", borderColor: "var(--border-color)" }}
        >
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={
              uploadStatus === "success" && uploadedFilename
                ? "Optional: Add any extra instructions or context here to guide the architecture generation..."
                : "Or simply explain your requirements here. What kind of system do you want to build?"
            }
            className="w-full flex-1 bg-transparent resize-none outline-none p-4 leading-relaxed text-sm"
            style={{ color: "var(--text-primary)" }}
          />
          
          {/* Character count footer */}
          <div className="px-4 py-2 flex justify-end items-center border-t border-transparent bg-transparent">
            <div
              className="text-[11px] font-mono px-2 py-0.5 rounded-full"
              style={{ background: "var(--bg-primary)", color: "var(--text-muted)", border: "1px solid var(--border-color)" }}
            >
              {value.length} chars
            </div>
          </div>
        </div>

      </div>
    </>
  );
}

"use client";

import { useRef, useState } from "react";
import { AlertCircle, CheckCircle2, FileText, Loader2, Upload, X } from "lucide-react";
import { errorMessage as toMessage, uploadDocument } from "@/lib/api";

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
    onDocumentUploaded?.("", "");

    try {
      const data = await uploadDocument(file);
      setUploadedFilename(data.filename || file.name);
      setUploadStatus("success");
      onDocumentUploaded?.(data.document_id, file.name);
    } catch (err: unknown) {
      setErrorMessage(toMessage(err, "Upload failed"));
      setUploadStatus("error");
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const clearFile = () => {
    setUploadStatus("idle");
    setUploadedFilename(null);
    setErrorMessage(null);
    onDocumentUploaded?.("", "");
  };

  const attached = uploadStatus === "success" && uploadedFilename;

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.md,.markdown,.txt,.docx,text/plain,text/markdown,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        className="hidden"
        onChange={handleFileSelect}
        id="srs-file-input"
      />

      <div className="panel-head">
        <FileText className="w-4 h-4" aria-hidden />
        <h2 className="panel-title">Requirements</h2>
        <span className="zone-tag" aria-label="Zone A1">A1</span>
      </div>

      <div className="flex-1 min-h-0 p-4 flex flex-col gap-3 overflow-y-auto">
        {attached ? (
          <div className="flex items-center gap-3 p-3 border" style={{ borderColor: "var(--ink)" }}>
            <CheckCircle2 className="w-5 h-5 shrink-0" style={{ color: "var(--ok)" }} aria-hidden />
            <div className="flex-1 min-w-0">
              <p className="font-semibold truncate">{uploadedFilename}</p>
              <p className="text-sm" style={{ color: "var(--ink-3)" }}>
                Attached. Text below is sent as extra instructions.
              </p>
            </div>
            <button onClick={clearFile} className="icon-btn" title="Remove file" aria-label="Remove file">
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadStatus === "uploading"}
            className="group flex items-center gap-4 p-4 text-left transition-colors hover:bg-[var(--paper-2)] disabled:cursor-wait"
            style={{ border: "1px dashed var(--ink)" }}
          >
            <span
              className="grid place-items-center w-11 h-11 shrink-0 border"
              style={{ borderColor: "var(--ink)" }}
            >
              {uploadStatus === "uploading" ? (
                <Loader2 className="w-5 h-5 animate-spin" aria-hidden />
              ) : (
                <Upload className="w-5 h-5 transition-transform group-hover:-translate-y-0.5" aria-hidden />
              )}
            </span>
            <span>
              <span className="block font-semibold">
                {uploadStatus === "uploading" ? "Uploading document…" : "Click to Upload SRS Document"}
              </span>
              <span className="block text-sm" style={{ color: "var(--ink-3)" }}>
                Attach a PDF, Word (.docx), Markdown, or Text file.
              </span>
            </span>
          </button>
        )}

        {uploadStatus === "error" && errorMessage && (
          <div
            role="alert"
            className="flex items-start gap-2 p-3 text-sm border"
            style={{ borderColor: "var(--danger)", color: "var(--danger)" }}
          >
            <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" aria-hidden />
            <span>{errorMessage}</span>
          </div>
        )}

        <div className="flex-1 flex flex-col min-h-[120px]">
          <label htmlFor="srs-text" className="field-label mb-1.5">
            {attached ? "Extra instructions" : "Or type requirements"}
          </label>
          <textarea
            id="srs-text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={
              attached
                ? "Optional: guide the architecture, for example “focus on the booking flow”."
                : "What kind of system do you want to build? Who uses it and what can they do?"
            }
            className="field flex-1 resize-none leading-relaxed"
          />
          <p className="mt-1.5 text-right text-xs tnum" style={{ color: "var(--ink-3)" }}>
            {value.length} chars
          </p>
        </div>
      </div>
    </>
  );
}

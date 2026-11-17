"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import InputPanel from "@/components/InputPanel";
import ExtractionPanel from "@/components/ExtractionPanel";
import MermaidPanel from "@/components/MermaidPanel";
import AgentLogs from "@/components/AgentLogs";
import AuthGuard from "@/components/AuthGuard";
import ThemeToggle from "@/components/ThemeToggle";
import { useAuth } from "@/contexts/AuthContext";
import { createTextDocument, errorMessage, getJob, startAnalysis } from "@/lib/api";
import type { JobResponse } from "@/types/api";
import { motion } from "framer-motion";
import { AlertTriangle, LogOut, User, Wand2, X } from "lucide-react";

const POLL_INTERVAL_MS = 2000;
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

function Dashboard() {
  const { user, logout } = useAuth();
  const [isProcessing, setIsProcessing] = useState(false);
  // Free text: the requirements themselves, or extra instructions when a file is attached.
  const [srsText, setSrsText] = useState("");
  const [uploadedDocId, setUploadedDocId] = useState<string | null>(null);
  const [job, setJob] = useState<JobResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Which document's log stream to show; `runId` remounts the log panel per run.
  const [streamDocId, setStreamDocId] = useState<string | null>(null);
  const [runId, setRunId] = useState(0);

  // Reuse the text document if the same text is generated twice.
  const textDocRef = useRef<{ text: string; id: string } | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  useEffect(() => () => abortRef.current?.abort(), []);

  const trimmed = srsText.trim();
  const canGenerate = !isProcessing && (!!uploadedDocId || trimmed.length > 0);

  const handleGenerate = async () => {
    if (!canGenerate) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setIsProcessing(true);
    setError(null);
    setJob(null);

    try {
      let documentId = uploadedDocId;
      let instructions = "";
      if (documentId) {
        instructions = trimmed;
      } else if (textDocRef.current?.text === trimmed) {
        documentId = textDocRef.current.id;
      } else {
        const doc = await createTextDocument(trimmed);
        documentId = doc.document_id;
        textDocRef.current = { text: trimmed, id: documentId };
      }

      const started = await startAnalysis(documentId, instructions);
      setRunId((n) => n + 1);
      setStreamDocId(documentId);

      // The pipeline runs in the background; poll until it finishes.
      let current = started;
      while (current.status === "queued" || current.status === "running") {
        await sleep(POLL_INTERVAL_MS);
        if (controller.signal.aborted) return;
        current = await getJob(started.job_id, controller.signal);
      }
      setJob(current);
      if (current.status === "failed") {
        setError(current.errors.join(" ") || "The analysis failed. Please try again.");
      }
    } catch (err) {
      if (controller.signal.aborted) return;
      setError(errorMessage(err, "The analysis failed. Please try again."));
    } finally {
      if (abortRef.current === controller) setIsProcessing(false);
    }
  };

  const warnings = job && job.status === "completed" ? job.errors : [];

  return (
    <div
      className="min-h-screen flex flex-col"
      style={{ background: "var(--bg-primary)", color: "var(--text-primary)" }}
    >
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <header
        className="sticky top-0 z-20 border-b px-4 md:px-8 py-3 flex items-center justify-between"
        style={{
          background: "var(--header-bg)",
          borderColor: "var(--border-color)",
          backdropFilter: "var(--glass-blur)",
          WebkitBackdropFilter: "var(--glass-blur)",
        }}
      >
        {/* Brand */}
        <div className="flex items-center gap-2.5">
          <Image
            src="/logo.png"
            alt="Structify logo"
            width={36}
            height={36}
            className="rounded-lg"
            priority
          />
          <div>
            <h1 className="text-base font-bold leading-tight" style={{ color: "var(--text-primary)" }}>
              Structify
            </h1>
            <p className="text-[11px] hidden sm:block" style={{ color: "var(--text-muted)" }}>
              AI-Powered System Design
            </p>
          </div>
        </div>

        {/* Right controls */}
        <div className="flex items-center gap-2">
          <ThemeToggle />

          {/* User info */}
          <div
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm"
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border-color)",
              color: "var(--text-secondary)",
            }}
          >
            <User className="w-3.5 h-3.5" />
            <span className="font-medium max-w-[120px] truncate">{user?.name}</span>
          </div>

          {/* Logout */}
          <button
            id="logout-button"
            onClick={logout}
            title="Sign out"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-all
              hover:!text-red-500 hover:!border-red-500/30"
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border-color)",
              color: "var(--text-secondary)",
            }}
          >
            <LogOut className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Sign out</span>
          </button>
        </div>
      </header>

      {/* ── Main Content ────────────────────────────────────────────────── */}
      <main className="flex-1 p-4 md:p-6 overflow-hidden">
        <div className="max-w-[1400px] mx-auto h-full flex flex-col gap-4" style={{ minHeight: "calc(100vh - 5rem)" }}>

          {(error || warnings.length > 0) && (
            <div
              role={error ? "alert" : "status"}
              className="flex items-start gap-2 px-4 py-3 rounded-xl text-sm border"
              style={
                error
                  ? { background: "rgba(239,68,68,0.1)", color: "#ef4444", borderColor: "rgba(239,68,68,0.25)" }
                  : { background: "rgba(234,179,8,0.1)", color: "#ca8a04", borderColor: "rgba(234,179,8,0.25)" }
              }
            >
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
              <div className="flex-1 space-y-0.5">
                {(error ? [error] : warnings).map((m) => (
                  <p key={m}>{m}</p>
                ))}
              </div>
              {error && (
                <button onClick={() => setError(null)} aria-label="Dismiss error" className="shrink-0">
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          )}

          {/* ── Row 1: Input (left) + Extraction (right) ── */}
          <div className="flex flex-col lg:flex-row gap-4 flex-1 min-h-0" style={{ flex: "0 0 auto", height: "clamp(360px, 45vh, 500px)" }}>

            {/* Input Panel */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
              className="glass-panel rounded-2xl overflow-hidden flex flex-col lg:w-[340px] lg:shrink-0"
            >
              <InputPanel
                value={srsText}
                onChange={setSrsText}
                onDocumentUploaded={(id) => setUploadedDocId(id || null)}
              />
              {/* Generate button inside panel footer */}
              <div
                className="p-3 border-t"
                style={{ borderColor: "var(--border-color)", background: "var(--bg-card)" }}
              >
                <button
                  id="generate-btn"
                  onClick={handleGenerate}
                  disabled={!canGenerate}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl
                    font-medium text-sm text-white bg-blue-600 hover:bg-blue-700
                    transition-all shadow-md hover:shadow-lg
                    disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ boxShadow: isProcessing ? "none" : "0 0 16px rgba(59,130,246,0.3)" }}
                >
                  <Wand2 className="w-4 h-4" />
                  {isProcessing ? "Processing…" : "Generate Architecture"}
                </button>
              </div>
            </motion.div>

            {/* Extraction Panel */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="glass-panel rounded-2xl overflow-hidden flex flex-col flex-1 min-w-0"
            >
              <ExtractionPanel isProcessing={isProcessing} data={job?.analysis ?? undefined} />
            </motion.div>
          </div>

          {/* ── Row 2: Diagrams (left) + Agent Logs (right) ── */}
          <div className="flex flex-col lg:flex-row gap-4 flex-1 min-h-0" style={{ flex: "1 1 0", minHeight: "280px" }}>

            {/* Mermaid/Visual panel */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
              className="glass-panel rounded-2xl overflow-hidden flex flex-col flex-1 min-w-0"
            >
              <MermaidPanel
                isProcessing={isProcessing}
                data={job?.diagrams}
                scaffoldData={job?.scaffold}
              />
            </motion.div>

            {/* Agent Logs */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="glass-panel rounded-2xl overflow-hidden flex flex-col lg:w-[300px] lg:shrink-0"
            >
              <AgentLogs key={runId} isProcessing={isProcessing} documentId={streamDocId} />
            </motion.div>
          </div>

        </div>
      </main>
    </div>
  );
}

export default function Home() {
  return (
    <AuthGuard>
      <Dashboard />
    </AuthGuard>
  );
}

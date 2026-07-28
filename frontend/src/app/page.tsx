"use client";

import { useState } from "react";
import InputPanel from "@/components/InputPanel";
import ExtractionPanel from "@/components/ExtractionPanel";
import MermaidPanel from "@/components/MermaidPanel";
import AgentLogs from "@/components/AgentLogs";
import AuthGuard from "@/components/AuthGuard";
import ThemeToggle from "@/components/ThemeToggle";
import { useAuth } from "@/contexts/AuthContext";
import { motion } from "framer-motion";
import { Code2, Wand2, LogOut, User } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function Dashboard() {
  const { user, logout } = useAuth();
  const [isProcessing, setIsProcessing] = useState(false);
  const [srsText, setSrsText] = useState("");
  const [documentId, setDocumentId] = useState<string | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [pipelineData, setPipelineData] = useState<any>(null);

  const handleGenerate = async () => {
    if (!documentId) {
      alert("Please upload an SRS document first.");
      return;
    }

    setIsProcessing(true);
    setPipelineData(null);

    // Give the SSE stream a moment to connect so we don't miss the initial events
    await new Promise((resolve) => setTimeout(resolve, 1000));

    try {
      const response = await fetch(`${API_URL}/api/analyze/full`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document_id: documentId }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      setPipelineData(data);
    } catch (err) {
      console.error("Pipeline failed:", err);
      alert(
        "Pipeline failed: " +
          (err instanceof Error ? err.message : String(err))
      );
    } finally {
      setIsProcessing(false);
    }
  };

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
          <div className="p-1.5 rounded-lg" style={{ background: "rgba(59,130,246,0.1)", border: "1px solid rgba(59,130,246,0.2)" }}>
            <Code2 className="w-5 h-5 text-blue-500" />
          </div>
          <div>
            <h1 className="text-base font-bold leading-tight" style={{ color: "var(--text-primary)" }}>
              Smart Doc Architect
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
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-all"
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border-color)",
              color: "var(--text-secondary)",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.color = "#ef4444";
              (e.currentTarget as HTMLButtonElement).style.borderColor = "rgba(239,68,68,0.3)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.color = "var(--text-secondary)";
              (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--border-color)";
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
                onDocumentUploaded={(id) => setDocumentId(id || null)}
              />
              {/* Generate button inside panel footer */}
              <div
                className="p-3 border-t"
                style={{ borderColor: "var(--border-color)", background: "var(--bg-card)" }}
              >
                <button
                  id="generate-btn"
                  onClick={handleGenerate}
                  disabled={isProcessing}
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
              <ExtractionPanel isProcessing={isProcessing} data={pipelineData?.analysis} />
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
                data={pipelineData?.diagrams}
                scaffoldData={pipelineData?.scaffold}
              />
            </motion.div>

            {/* Agent Logs */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="glass-panel rounded-2xl overflow-hidden flex flex-col lg:w-[300px] lg:shrink-0"
            >
              <AgentLogs isProcessing={isProcessing} documentId={documentId} />
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

"use client";

import { AlertTriangle, Download, ImageDown, Layout, Loader2, Maximize2, Minimize2 } from "lucide-react";
import dynamic from "next/dynamic";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { downloadScaffold, errorMessage } from "@/lib/api";
import type { Diagram, DiagramSetResponse, ScaffoldResponse } from "@/types/api";
import type { MermaidDiagramHandle } from "./MermaidDiagram";

const MermaidDiagram = dynamic(() => import("./MermaidDiagram"), { ssr: false });

interface MermaidPanelProps {
  isProcessing: boolean;
  data?: DiagramSetResponse | null;
  scaffoldData?: ScaffoldResponse | null;
}

// ─── Module-level components (defining them inside the panel would remount the
// diagram — and reset zoom/pan — on every state change) ───────────────────────

interface HeaderControlsProps {
  diagrams: Diagram[];
  current?: Diagram;
  onSelect: (id: string) => void;
  inModal?: boolean;
  isFullscreen: boolean;
  onToggleFullscreen: () => void;
  onDownloadPng: () => void;
  isDownloadingPng: boolean;
  scaffold?: ScaffoldResponse | null;
  onDownloadZip: () => void;
  isDownloadingZip: boolean;
}

function HeaderControls({
  diagrams,
  current,
  onSelect,
  inModal,
  isFullscreen,
  onToggleFullscreen,
  onDownloadPng,
  isDownloadingPng,
  scaffold,
  onDownloadZip,
  isDownloadingZip,
}: HeaderControlsProps) {
  return (
    <div className="flex items-center gap-2">
      {diagrams.length > 0 && (
        <select
          aria-label="Select diagram"
          className="text-xs rounded-md px-2 py-1 outline-none transition-colors"
          style={{
            background: "var(--input-bg)",
            border: "1px solid var(--border-color-strong)",
            color: "var(--text-primary)",
          }}
          value={current?.id ?? ""}
          onChange={(e) => onSelect(e.target.value)}
        >
          {diagrams.map((d) => (
            <option key={d.id} value={d.id}>
              {d.is_valid ? "" : "⚠ "}
              {d.title}
            </option>
          ))}
        </select>
      )}

      {current && (
        <button
          id={inModal ? "download-png-modal" : "download-png-btn"}
          onClick={onDownloadPng}
          disabled={isDownloadingPng}
          title="Download diagram as PNG"
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all
            disabled:opacity-50 disabled:cursor-not-allowed"
          style={{
            background: "rgba(59,130,246,0.12)",
            border: "1px solid rgba(59,130,246,0.3)",
            color: "#3b82f6",
          }}
        >
          <ImageDown className="w-3.5 h-3.5" />
          {isDownloadingPng ? "Saving…" : "PNG"}
        </button>
      )}

      {scaffold?.download_url && (
        <button
          id={inModal ? "download-zip-modal" : "download-zip-btn"}
          onClick={onDownloadZip}
          disabled={isDownloadingZip}
          title="Download the generated project as a ZIP"
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-white
            bg-green-600 hover:bg-green-700 transition-colors shadow-sm
            disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isDownloadingZip ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Download className="w-3.5 h-3.5" />
          )}
          ZIP
        </button>
      )}

      <button
        id={inModal ? "minimize-diagram" : "maximize-diagram"}
        onClick={onToggleFullscreen}
        aria-label={isFullscreen ? "Exit fullscreen" : "Expand to fullscreen"}
        className="p-1.5 rounded-lg transition-all hover:scale-105"
        style={{
          background: isFullscreen ? "rgba(59,130,246,0.15)" : "var(--bg-card-hover)",
          border: `1px solid ${isFullscreen ? "rgba(59,130,246,0.4)" : "var(--border-color)"}`,
        }}
        title={isFullscreen ? "Exit fullscreen (Esc)" : "Expand to fullscreen"}
      >
        {isFullscreen ? (
          <Minimize2 className="w-3.5 h-3.5" style={{ color: "#3b82f6" }} />
        ) : (
          <Maximize2 className="w-3.5 h-3.5" style={{ color: "var(--text-muted)" }} />
        )}
      </button>
    </div>
  );
}

function Warnings({ diagram, notes }: { diagram?: Diagram; notes: string[] }) {
  const lines = [
    ...(diagram && !diagram.is_valid
      ? [
          `This diagram may contain syntax errors${
            diagram.validation_errors.length ? `: ${diagram.validation_errors.join("; ")}` : "."
          }`,
        ]
      : []),
    ...notes,
  ];
  if (!lines.length) return null;
  return (
    <div
      role="status"
      className="flex items-start gap-2 px-4 py-2 text-xs border-b"
      style={{
        background: "rgba(234,179,8,0.1)",
        color: "#ca8a04",
        borderColor: "rgba(234,179,8,0.25)",
      }}
    >
      <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
      <div className="space-y-0.5">
        {lines.map((l) => (
          <p key={l}>{l}</p>
        ))}
      </div>
    </div>
  );
}

interface DiagramAreaProps {
  isProcessing: boolean;
  diagram?: Diagram;
  hasDiagrams: boolean;
  refHandle: React.Ref<MermaidDiagramHandle>;
}

function DiagramArea({ isProcessing, diagram, hasDiagrams, refHandle }: DiagramAreaProps) {
  return (
    <div className="flex-1 overflow-hidden flex items-center justify-center bg-[var(--input-bg)] relative">
      {isProcessing && !hasDiagrams ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center gap-4"
        >
          <div className="w-10 h-10 border-4 border-blue-500/25 border-t-blue-500 rounded-full animate-spin" />
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            Generating architecture diagrams…
          </p>
        </motion.div>
      ) : diagram ? (
        <div className="w-full h-full flex items-center justify-center">
          <MermaidDiagram ref={refHandle} chart={diagram.mermaid_code} />
        </div>
      ) : (
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          Diagrams will appear here after generation.
        </p>
      )}
    </div>
  );
}

// ─── Panel ──────────────────────────────────────────────────────────────────

export default function MermaidPanel({ isProcessing, data, scaffoldData }: MermaidPanelProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isDownloadingPng, setIsDownloadingPng] = useState(false);
  const [isDownloadingZip, setIsDownloadingZip] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Refs for the diagram instances inside and outside the modal
  const panelDiagramRef = useRef<MermaidDiagramHandle>(null);
  const modalDiagramRef = useRef<MermaidDiagramHandle>(null);

  const diagrams = data?.diagrams ?? [];
  // Falls back to the first diagram whenever the selection no longer exists
  // (for example after a new run), so no reset effect is needed.
  const current = diagrams.find((d) => d.id === selectedId) ?? diagrams[0];

  // Close fullscreen on Escape key
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsFullscreen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const handleDownloadPng = async () => {
    if (!current) return;
    setIsDownloadingPng(true);
    setActionError(null);
    const ref = isFullscreen ? modalDiagramRef : panelDiagramRef;
    const safeName = (current.title || "diagram").replace(/\s+/g, "_").toLowerCase();
    try {
      await ref.current?.downloadPng(`${safeName}.png`);
    } catch (err) {
      setActionError(errorMessage(err, "PNG export failed."));
    } finally {
      setIsDownloadingPng(false);
    }
  };

  const handleDownloadZip = async () => {
    if (!scaffoldData?.download_url) return;
    setIsDownloadingZip(true);
    setActionError(null);
    try {
      await downloadScaffold(scaffoldData.download_url, `${scaffoldData.project_name || "project"}.zip`);
    } catch (err) {
      setActionError(errorMessage(err, "ZIP download failed."));
    } finally {
      setIsDownloadingZip(false);
    }
  };

  const controls = (inModal: boolean) => (
    <HeaderControls
      diagrams={diagrams}
      current={current}
      onSelect={setSelectedId}
      inModal={inModal}
      isFullscreen={isFullscreen}
      onToggleFullscreen={() => setIsFullscreen((v) => !v)}
      onDownloadPng={handleDownloadPng}
      isDownloadingPng={isDownloadingPng}
      scaffold={scaffoldData}
      onDownloadZip={handleDownloadZip}
      isDownloadingZip={isDownloadingZip}
    />
  );

  const notes = [...(data?.errors ?? []), ...(actionError ? [actionError] : [])];

  return (
    <>
      {/* ── Inline panel (always rendered) ── */}
      <div
        className="px-4 py-3 border-b flex items-center justify-between"
        style={{ borderColor: "var(--border-color)", background: "var(--bg-card)" }}
      >
        <div className="flex items-center gap-2">
          <Layout className="w-4 h-4 text-blue-500" />
          <h2 className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>
            Architecture Diagrams
          </h2>
        </div>
        {controls(false)}
      </div>

      <Warnings diagram={current} notes={notes} />

      <DiagramArea
        isProcessing={isProcessing}
        diagram={current}
        hasDiagrams={diagrams.length > 0}
        refHandle={panelDiagramRef}
      />

      {/* ── Fullscreen modal ── */}
      <AnimatePresence>
        {isFullscreen && (
          <motion.div
            key="fullscreen-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 flex flex-col"
            style={{ background: "var(--bg-primary)" }}
          >
            <div
              className="flex items-center justify-between px-6 py-4 border-b shrink-0"
              style={{
                borderColor: "var(--border-color)",
                background: "var(--header-bg)",
                backdropFilter: "var(--glass-blur)",
              }}
            >
              <div className="flex items-center gap-3">
                <Layout className="w-5 h-5 text-blue-500" />
                <h2 className="font-semibold text-base" style={{ color: "var(--text-primary)" }}>
                  {current?.title || "Architecture Diagram"}
                </h2>
                <span
                  className="text-xs px-2 py-0.5 rounded-full"
                  style={{
                    background: "rgba(59,130,246,0.12)",
                    color: "#3b82f6",
                    border: "1px solid rgba(59,130,246,0.3)",
                  }}
                >
                  Fullscreen
                </span>
              </div>
              {controls(true)}
            </div>

            <Warnings diagram={current} notes={notes} />

            <div className="flex-1 overflow-hidden relative flex items-center justify-center bg-[var(--input-bg)]">
              {current ? (
                <MermaidDiagram ref={modalDiagramRef} chart={current.mermaid_code} />
              ) : (
                <p style={{ color: "var(--text-muted)" }}>No diagram selected.</p>
              )}
            </div>

            <div className="shrink-0 text-center py-2 text-xs" style={{ color: "var(--text-muted)" }}>
              Press{" "}
              <kbd
                className="px-1.5 py-0.5 rounded text-[10px] font-mono mx-1"
                style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)" }}
              >
                Esc
              </kbd>
              to close fullscreen
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

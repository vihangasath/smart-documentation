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
    <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto sm:justify-end">
      {diagrams.length > 0 && (
        <select
          aria-label="Select diagram"
          className="field !py-0 h-8 text-sm basis-full sm:basis-auto sm:!w-auto"
          value={current?.id ?? ""}
          onChange={(e) => onSelect(e.target.value)}
        >
          {diagrams.map((d) => (
            <option key={d.id} value={d.id}>
              {d.is_valid ? "" : "(invalid) "}
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
          className="btn-line"
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
          className="btn-line is-signal"
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
        className="icon-btn ml-auto sm:ml-0"
        title={isFullscreen ? "Exit fullscreen (Esc)" : "Expand to fullscreen"}
      >
        {isFullscreen ? (
          <Minimize2 className="w-4 h-4" />
        ) : (
          <Maximize2 className="w-4 h-4" />
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
      className="flex items-start gap-2 px-4 py-2 text-sm"
      style={{ color: "var(--warn)", borderBottom: "1px solid var(--rule)", background: "var(--paper-2)" }}
    >
      <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" aria-hidden />
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
    <div className="flex-1 min-h-[320px] lg:min-h-[260px] overflow-hidden flex items-center justify-center relative bg-[var(--paper-2)]">
      {isProcessing && !hasDiagrams ? (
        <div className="w-56" role="status">
          <div className="stage" data-state="live">
            <div className="stage-bar">
              <span className="stage-chip" />
            </div>
            <span className="stage-label">Drawing diagrams…</span>
          </div>
        </div>
      ) : diagram ? (
        // Absolutely positioned so the diagram can never size the panel: it
        // always fits the box the sheet gives it.
        <div className="absolute inset-0">
          <MermaidDiagram ref={refHandle} chart={diagram.mermaid_code} />
        </div>
      ) : (
        <>
          <span className="reg-mark tl" aria-hidden />
          <span className="reg-mark tr" aria-hidden />
          <span className="reg-mark bl" aria-hidden />
          <span className="reg-mark br" aria-hidden />
          <p style={{ color: "var(--ink-3)" }}>Diagrams will appear here after generation.</p>
        </>
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
      <div className="panel-head flex-wrap py-1.5">
        <Layout className="w-4 h-4" aria-hidden />
        <h2 className="panel-title">Architecture Diagrams</h2>
        <span className="zone-tag order-2 sm:order-none" aria-label="Zone A2">A2</span>
        <div className="order-3 sm:order-none w-full sm:w-auto sm:ml-4 pb-1 sm:pb-0">{controls(false)}</div>
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
            style={{ background: "var(--paper)" }}
          >
            <div className="panel-head py-2 shrink-0 flex-wrap">
              <Layout className="w-4 h-4" aria-hidden />
              <h2 className="panel-title">{current?.title || "Architecture Diagram"}</h2>
              <div className="ml-auto">{controls(true)}</div>
            </div>

            <Warnings diagram={current} notes={notes} />

            <div className="flex-1 overflow-hidden relative flex items-center justify-center bg-[var(--paper-2)]">
              {current ? (
                <MermaidDiagram ref={modalDiagramRef} chart={current.mermaid_code} />
              ) : (
                <p style={{ color: "var(--ink-3)" }}>No diagram selected.</p>
              )}
            </div>

            <div
              className="shrink-0 text-center py-2 text-xs"
              style={{ color: "var(--ink-3)", borderTop: "1px solid var(--rule)" }}
            >
              Press{" "}
              <kbd className="px-1.5 py-0.5 font-mono mx-1" style={{ border: "1px solid var(--ink-3)" }}>
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

"use client";

import { Layout, Maximize2, Minimize2, Download, ImageDown } from "lucide-react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useRef, useEffect } from "react";
import type { MermaidDiagramHandle } from "./MermaidDiagram";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const MermaidDiagram = dynamic(() => import("./MermaidDiagram"), { ssr: false });

interface Diagram {
  title: string;
  mermaid_code: string;
}

interface ScaffoldData {
  download_url?: string;
}

interface MermaidPanelProps {
  isProcessing: boolean;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data?: any;
  scaffoldData?: ScaffoldData;
}

export default function MermaidPanel({ isProcessing, data, scaffoldData }: MermaidPanelProps) {
  const [selectedDiagramIndex, setSelectedDiagramIndex] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  // Refs for the diagram instances inside and outside the modal
  const panelDiagramRef = useRef<MermaidDiagramHandle>(null);
  const modalDiagramRef = useRef<MermaidDiagramHandle>(null);

  const diagrams = data?.diagrams || [];
  const currentDiagram = diagrams[selectedDiagramIndex];

  // Close fullscreen on Escape key
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsFullscreen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const handleDownloadPng = async () => {
    if (!currentDiagram) return;
    setIsDownloading(true);
    const ref = isFullscreen ? modalDiagramRef : panelDiagramRef;
    const safeName = (currentDiagram.title || "diagram").replace(/\s+/g, "_").toLowerCase();
    try {
      await ref.current?.downloadPng(`${safeName}.png`);
    } finally {
      setIsDownloading(false);
    }
  };

  const HeaderControls = ({ inModal }: { inModal?: boolean }) => (
    <div className="flex items-center gap-2">
      {diagrams.length > 0 && (
        <select
          className="text-xs rounded-md px-2 py-1 outline-none transition-colors"
          style={{
            background: "var(--input-bg)",
            border: "1px solid var(--border-color-strong)",
            color: "var(--text-primary)",
          }}
          value={selectedDiagramIndex}
          onChange={(e) => setSelectedDiagramIndex(Number(e.target.value))}
        >
          {diagrams.map((d: Diagram, i: number) => (
            <option key={i} value={i}>{d.title}</option>
          ))}
        </select>
      )}

      {/* Download PNG button */}
      {currentDiagram && (
        <button
          id={inModal ? "download-png-modal" : "download-png-btn"}
          onClick={handleDownloadPng}
          disabled={isDownloading}
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
          {isDownloading ? "Saving…" : "PNG"}
        </button>
      )}

      {/* Download ZIP button */}
      {scaffoldData?.download_url && (
        <a
          href={`${API_URL}${scaffoldData.download_url}`}
          download
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-white
            bg-green-600 hover:bg-green-700 transition-colors shadow-sm"
        >
          <Download className="w-3.5 h-3.5" />
          ZIP
        </a>
      )}

      {/* Maximize / Minimize button */}
      <button
        id={inModal ? "minimize-diagram" : "maximize-diagram"}
        onClick={() => setIsFullscreen((v) => !v)}
        className="p-1.5 rounded-lg transition-all hover:scale-105"
        style={{
          background: isFullscreen ? "rgba(59,130,246,0.15)" : "var(--bg-card-hover)",
          border: `1px solid ${isFullscreen ? "rgba(59,130,246,0.4)" : "var(--border-color)"}`,
        }}
        title={isFullscreen ? "Exit fullscreen (Esc)" : "Expand to fullscreen"}
      >
        {isFullscreen
          ? <Minimize2 className="w-3.5 h-3.5" style={{ color: "#3b82f6" }} />
          : <Maximize2 className="w-3.5 h-3.5" style={{ color: "var(--text-muted)" }} />
        }
      </button>
    </div>
  );

  const DiagramArea = ({ refHandle }: { refHandle: React.Ref<MermaidDiagramHandle> }) => (
    <div
      className="flex-1 overflow-auto flex items-center justify-center p-6"
      style={{ background: "var(--input-bg)" }}
    >
      {isProcessing && diagrams.length === 0 ? (
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
      ) : currentDiagram ? (
        <div className="w-full h-full flex items-center justify-center">
          <MermaidDiagram ref={refHandle} chart={currentDiagram.mermaid_code} />
        </div>
      ) : (
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          Diagrams will appear here after generation.
        </p>
      )}
    </div>
  );

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
        <HeaderControls />
      </div>

      <DiagramArea refHandle={panelDiagramRef} />

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
            {/* Modal header */}
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
                  {currentDiagram?.title || "Architecture Diagram"}
                </h2>
                <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: "rgba(59,130,246,0.12)", color: "#3b82f6", border: "1px solid rgba(59,130,246,0.3)" }}>
                  Fullscreen
                </span>
              </div>
              <HeaderControls inModal />
            </div>

            {/* Modal body — diagram fills the rest */}
            <div className="flex-1 overflow-auto flex items-center justify-center p-8" style={{ background: "var(--input-bg)" }}>
              {currentDiagram ? (
                <MermaidDiagram ref={modalDiagramRef} chart={currentDiagram.mermaid_code} />
              ) : (
                <p style={{ color: "var(--text-muted)" }}>No diagram selected.</p>
              )}
            </div>

            {/* ESC hint */}
            <div className="shrink-0 text-center py-2 text-xs" style={{ color: "var(--text-muted)" }}>
              Press <kbd className="px-1.5 py-0.5 rounded text-[10px] font-mono mx-1"
                style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)" }}>Esc</kbd>
              to close fullscreen
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";
import LogoMark from "@/components/LogoMark";
import InputPanel from "@/components/InputPanel";
import ExtractionPanel from "@/components/ExtractionPanel";
import MermaidPanel from "@/components/MermaidPanel";
import AgentLogs from "@/components/AgentLogs";
import AuthGuard from "@/components/AuthGuard";
import ThemeToggle from "@/components/ThemeToggle";
import { useAuth } from "@/contexts/AuthContext";
import { createTextDocument, errorMessage, getJob, startAnalysis } from "@/lib/api";
import type { AgentEvent, JobResponse } from "@/types/api";
import { AlertTriangle, ArrowRight, LogOut, User, X } from "lucide-react";

const POLL_INTERVAL_MS = 1000;
type StageKey = "parse" | "diagram" | "scaffold";
type StageState = "pending" | "live" | "done" | "error";
type Stages = Record<StageKey, StageState>;

const IDLE_STAGES: Stages = { parse: "pending", diagram: "pending", scaffold: "pending" };
const STAGE_OF_AGENT: Record<string, StageKey> = {
  ParserAgent: "parse",
  DiagrammerAgent: "diagram",
  ScaffolderAgent: "scaffold",
};
const STAGE_LABELS: [StageKey, string][] = [
  ["parse", "Parse"],
  ["diagram", "Diagram"],
  ["scaffold", "Scaffold"],
];
const ZONES_TOP = ["A", "B", "C", "D"];

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
  const [stages, setStages] = useState<Stages>(IDLE_STAGES);

  // Stage state follows the agent events; a stage that finished stays lit.
  const handleAgentEvent = (e: AgentEvent) => {
    const key = STAGE_OF_AGENT[e.agent_name];
    if (e.type === "pipeline_error") {
      setStages((s) => {
        const next = { ...s };
        (Object.keys(next) as StageKey[]).forEach((k) => {
          if (next[k] === "live") next[k] = "error";
        });
        return next;
      });
    } else if (key) {
      const state: StageState | null =
        e.type === "agent_start" ? "live" : e.type === "agent_complete" ? "done" : e.type === "agent_error" ? "error" : null;
      if (state) setStages((s) => ({ ...s, [key]: state }));
    }
  };

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
    setStages(IDLE_STAGES);

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
        // Results arrive stage by stage, so panels fill as soon as they exist.
        setJob(current);
      }
      setJob(current);
      // Settle the title block from the final result (covers a missed stream).
      setStages({
        parse: current.analysis ? "done" : "error",
        diagram: current.diagrams ? "done" : current.analysis ? "error" : "pending",
        scaffold: current.scaffold ? "done" : current.analysis ? "error" : "pending",
      });
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

  const statusText = isProcessing
    ? "Running"
    : job?.status === "completed"
      ? warnings.length
        ? "Complete with notes"
        : "Complete"
      : job?.status === "failed"
        ? "Failed"
        : "Idle";

  return (
    <div className="min-h-screen lg:h-screen lg:min-h-[780px] p-2 sm:p-3 flex flex-col">
      <div className="sheet-frame flex-1 min-h-0 flex flex-col">
        {/* ── Header strip ─────────────────────────────────────────────── */}
        <header className="flex items-center justify-between gap-3 px-3 sm:px-4 py-2.5">
          <div className="flex items-center gap-2.5 min-w-0">
            <LogoMark size={34} className="shrink-0" />
            <h1 className="font-cond text-2xl font-semibold leading-none tracking-tight">Structify</h1>
            <p className="hidden md:block text-sm pl-3 ml-1 border-l" style={{ color: "var(--ink-3)", borderColor: "var(--rule)" }}>
              AI-powered system design
            </p>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <span
              className="hidden sm:flex items-center gap-2 h-8 px-3 text-sm border"
              style={{ borderColor: "var(--rule)", color: "var(--ink-2)" }}
            >
              <User className="w-3.5 h-3.5" aria-hidden />
              <span className="font-semibold max-w-[120px] truncate">{user?.name}</span>
            </span>
            <button id="logout-button" onClick={logout} title="Sign out" className="btn-line">
              <LogOut className="w-3.5 h-3.5" aria-hidden />
              <span className="hidden sm:inline">Sign out</span>
            </button>
          </div>
        </header>

        {(error || warnings.length > 0) && (
          <div
            role={error ? "alert" : "status"}
            className="flex items-start gap-2 px-4 py-2.5 text-sm"
            style={{
              borderTop: "1px solid var(--rule)",
              color: error ? "var(--danger)" : "var(--warn)",
              background: "var(--paper-2)",
            }}
          >
            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" aria-hidden />
            <div className="flex-1 space-y-0.5">
              {(error ? [error] : warnings).map((m) => (
                <p key={m}>{m}</p>
              ))}
            </div>
            {error && (
              <button onClick={() => setError(null)} aria-label="Dismiss error" className="icon-btn !border-0">
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        )}

        {/* ── The sheet ────────────────────────────────────────────────── */}
        <main
          className="sheet-grid flex-1 min-h-0 lg:grid-cols-[28px_repeat(12,minmax(0,1fr))] lg:grid-rows-[26px_minmax(330px,40vh)_minmax(280px,1fr)_auto]"
        >
          {/* top ruler */}
          <div className="hidden lg:block" aria-hidden />
          {ZONES_TOP.map((z) => (
            <div
              key={z}
              aria-hidden
              className="hidden lg:grid lg:col-span-3 place-items-center font-cond font-semibold text-sm tracking-widest"
              style={{ color: "var(--ink-3)" }}
            >
              {z}
            </div>
          ))}

          {/* row 1 */}
          <div className="hidden lg:grid place-items-center font-cond font-semibold text-sm" aria-hidden style={{ color: "var(--ink-3)" }}>
            1
          </div>
          <section className="flex flex-col min-h-0 lg:col-span-6" aria-label="Requirements">
            <InputPanel value={srsText} onChange={setSrsText} onDocumentUploaded={(id) => setUploadedDocId(id || null)} />
            <div className="p-4" style={{ borderTop: "1px solid var(--rule)" }}>
              <button id="generate-btn" onClick={handleGenerate} disabled={!canGenerate} className="btn-signal">
                {isProcessing ? "Processing…" : "Generate Architecture"}
                {!isProcessing && <ArrowRight className="w-5 h-5 arrow" aria-hidden />}
              </button>
            </div>
          </section>
          <section className="flex flex-col lg:min-h-0 lg:col-span-6" aria-label="Extraction">
            <ExtractionPanel isProcessing={isProcessing} data={job?.analysis ?? undefined} />
          </section>

          {/* row 2 */}
          <div className="hidden lg:grid place-items-center font-cond font-semibold text-sm" aria-hidden style={{ color: "var(--ink-3)" }}>
            2
          </div>
          <section className="flex flex-col min-h-0 lg:col-span-9" aria-label="Diagrams">
            <MermaidPanel isProcessing={isProcessing} data={job?.diagrams} scaffoldData={job?.scaffold} />
          </section>
          <section className="flex flex-col lg:col-span-3 min-h-[200px] lg:min-h-0" aria-label="Agent logs">
            <AgentLogs key={runId} isProcessing={isProcessing} documentId={streamDocId} onEvent={handleAgentEvent} />
          </section>

          {/* title block */}
          <div className="hidden lg:block" aria-hidden />
          <section
            className="lg:col-span-12 grid gap-x-8 gap-y-3 px-4 py-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)_auto] items-end"
            aria-label="Title block"
          >
            <div className="min-w-0">
              <p className="field-label">Project</p>
              <p className="font-cond text-3xl font-bold leading-tight truncate">
                {job?.analysis?.project_name || "Untitled sheet"}
              </p>
            </div>
            <div className="grid grid-cols-3 gap-3" role="list" aria-label="Pipeline stages">
              {STAGE_LABELS.map(([key, label]) => (
                <div key={key} className="stage" data-state={stages[key]} role="listitem">
                  <div className="stage-bar">{stages[key] === "live" && <span className="stage-chip" />}</div>
                  <span className="stage-label">
                    {label}
                    <span className="sr-only"> {stages[key]}</span>
                  </span>
                </div>
              ))}
            </div>
            <dl className="grid grid-cols-2 gap-x-6 lg:text-right">
              <div>
                <dt className="field-label">Status</dt>
                <dd className="font-semibold">{statusText}</dd>
              </div>
              <div>
                <dt className="field-label">Rev</dt>
                <dd className="font-semibold tnum">{String(runId).padStart(2, "0")}</dd>
              </div>
            </dl>
          </section>
        </main>
      </div>
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

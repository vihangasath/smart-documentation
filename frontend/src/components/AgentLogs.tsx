"use client";

import { Terminal } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { streamEvents } from "@/lib/api";
import type { AgentEvent } from "@/types/api";

interface AgentLogsProps {
  isProcessing: boolean;
  /** Document whose agent events are streamed. Remount (key) to start a new run. */
  documentId?: string | null;
  /** Called for every distinct agent event (used by the title block). */
  onEvent?: (event: AgentEvent) => void;
}

interface LogLine {
  agent: string;
  msg: string;
  time: string;
  type: string;
}

// Each agent reports into a sheet zone; the log cites it like an index of plates.
const AGENT_ZONES: Record<string, string> = {
  ParserAgent: "C1",
  DiagrammerAgent: "A2",
  ScaffolderAgent: "A2",
};

const RECONNECT_DELAY_MS = 1500;
const MAX_RECONNECTS = 5;

function formatTime(iso: string): string {
  const d = iso ? new Date(iso) : new Date();
  return Number.isNaN(d.getTime())
    ? ""
    : d.toLocaleTimeString([], { hour12: false });
}

export default function AgentLogs({ isProcessing, documentId, onEvent: onAgentEvent }: AgentLogsProps) {
  const [logs, setLogs] = useState<LogLine[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!documentId) return;

    const controller = new AbortController();
    // The server replays history on every (re)connect, so de-duplicate.
    const seen = new Set<string>();
    const add = (agent: string, msg: string, iso = "", type = "info") =>
      setLogs((prev) => [...prev, { agent: agent || "System", msg, time: formatTime(iso), type }]);

    const onEvent = (e: AgentEvent) => {
      const key = `${e.timestamp}|${e.type}|${e.message}`;
      if (seen.has(key)) return;
      seen.add(key);
      add(e.agent_name, e.message, e.timestamp, e.type);
      onAgentEvent?.(e);
    };

    async function run() {
      for (let attempt = 0; attempt <= MAX_RECONNECTS; attempt++) {
        try {
          if (await streamEvents(documentId as string, onEvent, controller.signal)) return;
        } catch (err) {
          if (controller.signal.aborted) return;
          if (attempt === MAX_RECONNECTS) {
            add("System", `Log stream unavailable: ${err instanceof Error ? err.message : err}`);
            return;
          }
        }
        if (controller.signal.aborted) return;
        await new Promise((r) => setTimeout(r, RECONNECT_DELAY_MS));
      }
      add("System", "Log stream disconnected.");
    }

    void run();
    return () => controller.abort();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <>
      <div className="panel-head">
        <Terminal className="w-4 h-4" aria-hidden />
        <h2 className="panel-title">Agent Logs</h2>
        <span className="flex items-center gap-1.5 text-sm" style={{ color: "var(--ink-3)" }}>
          <span
            aria-hidden
            className={`inline-block w-2 h-2 rounded-full ${isProcessing ? "animate-pulse" : ""}`}
            style={{ background: isProcessing ? "var(--signal)" : "var(--rule)" }}
          />
          {isProcessing ? "Live" : "Idle"}
        </span>
        <span className="zone-tag" aria-label="Zone D2">D2</span>
      </div>

      <div
        ref={scrollRef}
        role="log"
        aria-live="polite"
        className="flex-1 min-h-0 max-h-72 lg:max-h-none px-4 py-3 font-mono text-xs overflow-auto space-y-2"
        style={{ background: "var(--log-bg)" }}
      >
        <AnimatePresence initial={false}>
          {logs.map((log, idx) => {
            const zone = AGENT_ZONES[log.agent];
            const isError = log.type === "agent_error" || log.type === "pipeline_error";
            return (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
                className="leading-snug"
                style={{ color: isError ? "var(--danger)" : "var(--ink)" }}
              >
                <span className="tnum" style={{ color: "var(--ink-3)" }}>
                  {log.time}
                </span>{" "}
                <span className="font-semibold">{log.agent}</span>
                {zone && <span style={{ color: "var(--ink-3)" }}> [{zone}]</span>}{" "}
                {log.type === "agent_complete" && (
                  <span aria-hidden style={{ color: "var(--signal)" }}>
                    ■{" "}
                  </span>
                )}
                <span style={{ color: isError ? "var(--danger)" : "var(--ink-2)" }}>{log.msg}</span>
              </motion.div>
            );
          })}
        </AnimatePresence>
        {!isProcessing && logs.length === 0 && (
          <p style={{ color: "var(--ink-3)" }}>Waiting for generation to start…</p>
        )}
      </div>
    </>
  );
}

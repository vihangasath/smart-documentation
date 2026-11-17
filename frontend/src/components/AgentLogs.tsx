"use client";

import { Terminal } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { streamEvents } from "@/lib/api";
import type { AgentEvent } from "@/types/api";

interface AgentLogsProps {
  isProcessing: boolean;
  /** Document whose agent events are streamed. Remount (key) to start a new run. */
  documentId?: string | null;
}

interface LogLine {
  agent: string;
  msg: string;
  time: string;
}

const AGENT_COLORS: Record<string, string> = {
  Lead: "#3b82f6",
  ParserAgent: "#a855f7",
  DiagrammerAgent: "#eab308",
  ScaffolderAgent: "#ec4899",
  System: "#64748b",
};

const RECONNECT_DELAY_MS = 1500;
const MAX_RECONNECTS = 5;

function formatTime(iso: string): string {
  const d = iso ? new Date(iso) : new Date();
  return Number.isNaN(d.getTime())
    ? ""
    : d.toLocaleTimeString([], { hour12: false });
}

export default function AgentLogs({ isProcessing, documentId }: AgentLogsProps) {
  const [logs, setLogs] = useState<LogLine[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!documentId) return;

    const controller = new AbortController();
    // The server replays history on every (re)connect, so de-duplicate.
    const seen = new Set<string>();
    const add = (agent: string, msg: string, iso = "") =>
      setLogs((prev) => [...prev, { agent: agent || "System", msg, time: formatTime(iso) }]);

    const onEvent = (e: AgentEvent) => {
      const key = `${e.timestamp}|${e.type}|${e.message}`;
      if (seen.has(key)) return;
      seen.add(key);
      add(e.agent_name, e.message, e.timestamp);
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
  }, [documentId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <>
      {/* Header */}
      <div
        className="px-4 py-3 border-b flex items-center justify-between"
        style={{ borderColor: "var(--border-color)", background: "var(--bg-card)" }}
      >
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-green-500" />
          <h2 className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>
            Agent Logs
          </h2>
        </div>
        <div className="flex items-center gap-1.5">
          <div
            className={`w-2 h-2 rounded-full ${
              isProcessing ? "bg-green-500 animate-pulse" : "bg-gray-400"
            }`}
          />
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            {isProcessing ? "Live" : "Idle"}
          </span>
        </div>
      </div>

      {/* Log output */}
      <div
        ref={scrollRef}
        className="flex-1 p-3 font-mono text-xs overflow-auto space-y-1.5"
        style={{ background: "var(--terminal-bg)" }}
      >
        <AnimatePresence initial={false}>
          {logs.map((log, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex gap-2"
            >
              {log.time && (
                <span style={{ color: "var(--text-muted)" }} className="shrink-0">
                  [{log.time}]
                </span>
              )}
              <span
                className="shrink-0"
                style={{ color: AGENT_COLORS[log.agent] || AGENT_COLORS.System }}
              >
                &lt;{log.agent}&gt;
              </span>
              <span style={{ color: "var(--terminal-text)" }}>{log.msg}</span>
            </motion.div>
          ))}
        </AnimatePresence>
        {!isProcessing && logs.length === 0 && (
          <div style={{ color: "var(--text-muted)" }}>Waiting for generation to start…</div>
        )}
      </div>
    </>
  );
}

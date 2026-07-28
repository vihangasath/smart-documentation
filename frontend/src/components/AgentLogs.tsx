import { Terminal } from "lucide-react";
import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AgentLogsProps {
  isProcessing: boolean;
  documentId?: string | null;
}

const AGENT_COLORS: Record<string, string> = {
  Lead: "#3b82f6",
  ParserAgent: "#a855f7",
  DiagrammerAgent: "#eab308",
  ScaffolderAgent: "#ec4899",
  System: "#64748b",
};

export default function AgentLogs({ isProcessing }: AgentLogsProps) {
  const [logs, setLogs] = useState<{ agent: string; msg: string }[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isProcessing) return;

    const timer = setTimeout(() => {
      setLogs([{ agent: "System", msg: "Connecting to SSE stream…" }]);
    }, 0);

    const eventSource = new EventSource(`${API_URL}/api/events`);

    const handleMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        setLogs((prev) => [...prev, { agent: data.agent_name, msg: data.message }]);
      } catch (err) {
        console.error("Failed to parse SSE message", err);
      }
    };

    const eventTypes = [
      "agent_start", "agent_progress", "agent_complete", "agent_error",
      "pipeline_start", "pipeline_complete", "pipeline_error",
    ];

    eventTypes.forEach((type) => eventSource.addEventListener(type, handleMessage));

    eventSource.onopen = () => {
      setLogs((prev) => [...prev, { agent: "System", msg: "Stream connected. Awaiting events…" }]);
    };
    eventSource.onmessage = handleMessage;
    eventSource.onerror = () => {
      setLogs((prev) => [...prev, { agent: "System", msg: "Stream disconnected." }]);
      eventSource.close();
    };

    return () => {
      clearTimeout(timer);
      eventSource.close();
    };
  }, [isProcessing]);

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
        <AnimatePresence>
          {logs.map((log, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex gap-2"
            >
              <span style={{ color: "var(--text-muted)" }} className="shrink-0">
                [{new Date().toLocaleTimeString([], { hour12: false })}]
              </span>
              <span
                className="shrink-0"
                style={{ color: AGENT_COLORS[log?.agent] || AGENT_COLORS.System }}
              >
                &lt;{log?.agent || "System"}&gt;
              </span>
              <span style={{ color: "var(--terminal-text)" }}>{log?.msg || ""}</span>
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

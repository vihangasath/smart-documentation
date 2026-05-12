import { Terminal } from "lucide-react";
import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AgentLogsProps {
  isProcessing: boolean;
  documentId?: string | null;
}

export default function AgentLogs({ isProcessing }: AgentLogsProps) {
  const [logs, setLogs] = useState<{agent: string, msg: string}[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isProcessing) {
      // Don't clear logs immediately if processing finishes,
      // so the user can see the final logs.
      return;
    }

    // Delaying the initial state update to avoid synchronous setState during effect
    const timer = setTimeout(() => {
      setLogs([{ agent: "System", msg: "Connecting to SSE stream..." }]);
    }, 0);
    
    const eventSource = new EventSource(`${API_URL}/api/events`);
    
    const handleMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        setLogs(prev => [...prev, { agent: data.agent_name, msg: data.message }]);
      } catch (err) {
        console.error("Failed to parse SSE message", err);
      }
    };

    // Listen to all possible event types emitted by the backend
    const eventTypes = [
      "agent_start", "agent_progress", "agent_complete", "agent_error",
      "pipeline_start", "pipeline_complete", "pipeline_error"
    ];

    eventTypes.forEach(type => {
      eventSource.addEventListener(type, handleMessage);
    });
    
    eventSource.onopen = () => {
      setLogs(prev => [...prev, { agent: "System", msg: "Stream connected. Awaiting events..." }]);
    };

    // Also keep onmessage as fallback
    eventSource.onmessage = handleMessage;
    
    eventSource.onerror = () => {
      setLogs(prev => [...prev, { agent: "System", msg: "Stream disconnected or error occurred." }]);
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
      <div className="p-4 border-b border-white/10 flex items-center justify-between bg-black/20">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-green-400" />
          <h2 className="font-semibold">Agent Logs (Live Stream)</h2>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isProcessing ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`} />
          <span className="text-xs text-gray-400">{isProcessing ? 'Connected' : 'Offline'}</span>
        </div>
      </div>
      <div 
        ref={scrollRef}
        className="flex-1 p-4 bg-black/60 font-mono text-sm overflow-auto text-green-400 space-y-2"
      >
        <AnimatePresence>
          {logs.map((log, idx) => (
            <motion.div 
              key={idx}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex gap-3"
            >
              <span className="text-gray-500 shrink-0">
                [{new Date().toLocaleTimeString([], { hour12: false })}]
              </span>
              <span className={`shrink-0 ${
                log?.agent === 'Lead' ? 'text-blue-400' :
                log?.agent === 'ParserAgent' ? 'text-purple-400' :
                log?.agent === 'DiagrammerAgent' ? 'text-yellow-400' :
                log?.agent === 'ScaffolderAgent' ? 'text-pink-400' :
                'text-gray-400'
              }`}>
                &lt;{log?.agent || 'System'}&gt;
              </span>
              <span className="text-green-300">{log?.msg || ''}</span>
            </motion.div>
          ))}
        </AnimatePresence>
        {!isProcessing && logs.length === 0 && (
          <div className="text-gray-600">Waiting for generation to start...</div>
        )}
      </div>
    </>
  );
}

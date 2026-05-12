"use client";

import { useState } from "react";
import InputPanel from "@/components/InputPanel";
import ExtractionPanel from "@/components/ExtractionPanel";
import MermaidPanel from "@/components/MermaidPanel";
import AgentLogs from "@/components/AgentLogs";
import { motion } from "framer-motion";
import { Code2, Wand2 } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
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
    await new Promise(resolve => setTimeout(resolve, 1000));

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
      alert("Pipeline failed: " + (err instanceof Error ? err.message : String(err)));
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen text-foreground p-4 md:p-8">
      <header className="max-w-7xl mx-auto mb-8 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-white/10 rounded-xl glass-panel">
            <Code2 className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
              Smart Documentation Architect
            </h1>
            <p className="text-sm text-gray-400">AI-Powered System Design Orchestrator</p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto h-[calc(100vh-8rem)]">
        <div className="grid grid-cols-1 lg:grid-cols-12 grid-rows-1 lg:grid-rows-3 gap-6 h-full">
          
          {/* Top Left: Input Panel */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="lg:col-span-4 lg:row-span-2 glass-panel rounded-2xl overflow-hidden flex flex-col"
          >
            <InputPanel
              value={srsText}
              onChange={setSrsText}
              onDocumentUploaded={(id) => setDocumentId(id || null)}
            />
            <div className="p-4 border-t border-white/10 bg-black/20 mt-auto">
              <button 
                onClick={handleGenerate}
                disabled={isProcessing}
                className="w-full flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 transition-all font-medium shadow-[0_0_20px_rgba(37,99,235,0.3)] hover:shadow-[0_0_25px_rgba(37,99,235,0.5)] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Wand2 className="w-5 h-5" />
                {isProcessing ? "Processing..." : "Generate Architecture"}
              </button>
            </div>
          </motion.div>

          {/* Top Right: Logic/Extraction */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="lg:col-span-8 lg:row-span-1 glass-panel rounded-2xl overflow-hidden flex flex-col"
          >
            <ExtractionPanel isProcessing={isProcessing} data={pipelineData?.analysis} />
          </motion.div>

          {/* Bottom Right: Visual Output (Mermaid) */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="lg:col-span-8 lg:row-span-2 glass-panel rounded-2xl overflow-hidden flex flex-col"
          >
            <MermaidPanel isProcessing={isProcessing} data={pipelineData?.diagrams} scaffoldData={pipelineData?.scaffold} />
          </motion.div>

          {/* Bottom Left: Agent Logs (Live Stream) */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="lg:col-span-4 lg:row-span-1 glass-panel rounded-2xl overflow-hidden flex flex-col"
          >
            <AgentLogs isProcessing={isProcessing} documentId={documentId} />
          </motion.div>

        </div>
      </main>
    </div>
  );
}

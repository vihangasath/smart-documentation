import { Layout, Maximize2, Download } from "lucide-react";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { useState } from "react";

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

  const diagrams = data?.diagrams || [];
  const currentDiagram = diagrams[selectedDiagramIndex];

  return (
    <>
      <div className="p-4 border-b border-white/10 flex items-center justify-between bg-black/20">
        <div className="flex items-center gap-2">
          <Layout className="w-5 h-5 text-blue-400" />
          <h2 className="font-semibold">Visual Output & Scaffold</h2>
        </div>
        <div className="flex items-center gap-3">
          {diagrams.length > 0 && (
            <select 
              className="bg-black/40 border border-white/10 rounded-md px-2 py-1 text-sm outline-none text-white"
              value={selectedDiagramIndex}
              onChange={(e) => setSelectedDiagramIndex(Number(e.target.value))}
            >
              {diagrams.map((d: Diagram, i: number) => (
                <option key={i} value={i}>{d.title}</option>
              ))}
            </select>
          )}

          {scaffoldData?.download_url && (
            <a 
              href={`${API_URL}${scaffoldData.download_url}`}
              download
              className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded-md text-sm transition-colors shadow-lg"
            >
              <Download className="w-4 h-4" />
              Download ZIP
            </a>
          )}
          <button className="p-1.5 hover:bg-white/10 rounded-lg transition-colors">
            <Maximize2 className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </div>
      <div className="flex-1 p-4 bg-white/5 overflow-auto flex items-center justify-center relative">
        {isProcessing && diagrams.length === 0 ? (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center gap-4 text-blue-400"
          >
            <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
            <p>Architect Agent is designing...</p>
          </motion.div>
        ) : currentDiagram ? (
          <MermaidDiagram chart={currentDiagram.mermaid_code} />
        ) : (
          <div className="text-gray-500">
            Diagrams will appear here once generated.
          </div>
        )}
      </div>
    </>
  );
}

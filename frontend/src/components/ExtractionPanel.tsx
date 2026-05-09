import { Database, Code, Link2, Zap, ChevronDown, ChevronRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";

interface Attribute {
  name: string;
  data_type: string;
  is_required: boolean;
  description?: string;
}

interface Entity {
  name: string;
  description?: string;
  attributes: Attribute[];
}

interface Relationship {
  source: string;
  target: string;
  relationship_type: string;
  label?: string;
}

interface Action {
  name: string;
  description?: string;
  actor?: string;
  target_entity?: string;
  http_method: string;
  endpoint: string;
}

interface ExtractionPanelProps {
  isProcessing: boolean;
  data?: {
    project_name?: string;
    description?: string;
    entities?: Entity[];
    relationships?: Relationship[];
    actions?: Action[];
    entity_count?: number;
    relationship_count?: number;
    action_count?: number;
  };
}

type Tab = "entities" | "relationships" | "actions";

const METHOD_COLORS: Record<string, string> = {
  GET:    "bg-blue-500/20 text-blue-300 border-blue-500/40",
  POST:   "bg-green-500/20 text-green-300 border-green-500/40",
  PUT:    "bg-yellow-500/20 text-yellow-300 border-yellow-500/40",
  PATCH:  "bg-orange-500/20 text-orange-300 border-orange-500/40",
  DELETE: "bg-red-500/20 text-red-300 border-red-500/40",
};

function EntityCard({ entity }: { entity: Entity }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-white/10 rounded-lg overflow-hidden mb-2">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-3 py-2 bg-white/5 hover:bg-white/10 transition-colors text-left"
      >
        <div className="flex items-center gap-2">
          <Database className="w-3.5 h-3.5 text-purple-400 shrink-0" />
          <span className="font-medium text-white text-sm">{entity.name}</span>
          <span className="text-xs text-gray-500">({entity.attributes.length} attrs)</span>
        </div>
        {open ? <ChevronDown className="w-3.5 h-3.5 text-gray-500" /> : <ChevronRight className="w-3.5 h-3.5 text-gray-500" />}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            {entity.description && (
              <p className="px-3 pt-2 text-xs text-gray-400 italic">{entity.description}</p>
            )}
            <div className="px-3 py-2 space-y-1">
              {entity.attributes.map((attr) => (
                <div key={attr.name} className="flex items-center gap-2 text-xs">
                  <span className="text-gray-300 font-mono">{attr.name}</span>
                  <span className="text-purple-400 font-mono">:{attr.data_type}</span>
                  {attr.is_required && (
                    <span className="text-red-400 text-[10px]">required</span>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function ExtractionPanel({ isProcessing, data }: ExtractionPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>("entities");

  const entities = data?.entities || [];
  const relationships = data?.relationships || [];
  const actions = data?.actions || [];

  const tabs: { key: Tab; label: string; count: number; icon: React.ReactNode; color: string }[] = [
    { key: "entities", label: "Entities", count: data?.entity_count ?? entities.length, icon: <Database className="w-3 h-3" />, color: "text-purple-400 border-purple-500" },
    { key: "relationships", label: "Relations", count: data?.relationship_count ?? relationships.length, icon: <Link2 className="w-3 h-3" />, color: "text-blue-400 border-blue-500" },
    { key: "actions", label: "Actions", count: data?.action_count ?? actions.length, icon: <Zap className="w-3 h-3" />, color: "text-yellow-400 border-yellow-500" },
  ];

  return (
    <>
      {/* Header */}
      <div className="p-3 border-b border-white/10 bg-black/20">
        <div className="flex items-center gap-2 mb-2">
          <Database className="w-4 h-4 text-purple-400" />
          <h2 className="font-semibold text-sm">
            Logic Extraction
            {data?.project_name && (
              <span className="ml-2 text-gray-400 font-normal text-xs">— {data.project_name}</span>
            )}
          </h2>
        </div>
        {/* Tabs */}
        <div className="flex gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-md border transition-all ${
                activeTab === tab.key
                  ? `${tab.color} bg-white/10`
                  : "text-gray-500 border-transparent hover:text-gray-300 hover:bg-white/5"
              }`}
            >
              {tab.icon}
              {tab.label}
              {data && (
                <span className={`px-1 py-0 rounded text-[10px] font-bold ${activeTab === tab.key ? "" : "opacity-60"}`}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 p-3 bg-black/40 overflow-auto">
        {isProcessing && !data ? (
          <div className="flex items-center gap-2 text-purple-400 text-sm">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
            >
              <Code className="w-4 h-4" />
            </motion.div>
            <span>Extracting bounded contexts and domain entities...</span>
          </div>
        ) : data ? (
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.15 }}
            >
              {activeTab === "entities" && (
                entities.length > 0 ? (
                  entities.map((e) => <EntityCard key={e.name} entity={e} />)
                ) : (
                  <p className="text-gray-500 text-xs">No entities extracted.</p>
                )
              )}

              {activeTab === "relationships" && (
                relationships.length > 0 ? (
                  <div className="space-y-2">
                    {relationships.map((r, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs border border-white/10 rounded-lg px-3 py-2 bg-white/5">
                        <span className="text-blue-300 font-medium">{r.source}</span>
                        <span className="text-gray-500">—{r.relationship_type}→</span>
                        <span className="text-blue-300 font-medium">{r.target}</span>
                        {r.label && <span className="text-gray-500 italic ml-auto">{r.label}</span>}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-xs">No relationships extracted.</p>
                )
              )}

              {activeTab === "actions" && (
                actions.length > 0 ? (
                  <div className="space-y-2">
                    {actions.map((a, i) => (
                      <div key={i} className="border border-white/10 rounded-lg px-3 py-2 bg-white/5 text-xs">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`px-1.5 py-0.5 rounded border font-bold font-mono text-[10px] ${METHOD_COLORS[a.http_method] || "bg-gray-500/20 text-gray-300 border-gray-500/40"}`}>
                            {a.http_method}
                          </span>
                          <span className="text-yellow-300 font-mono">{a.endpoint}</span>
                        </div>
                        <div className="text-white font-medium">{a.name}</div>
                        {a.description && <div className="text-gray-400 mt-0.5">{a.description}</div>}
                        {a.actor && <div className="text-gray-500 mt-0.5">Actor: {a.actor} → {a.target_entity}</div>}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-xs">No actions extracted.</p>
                )
              )}
            </motion.div>
          </AnimatePresence>
        ) : (
          <div className="text-gray-600 text-xs font-mono">
            {"// Upload an SRS document and click Generate Architecture\n// Extracted entities, relationships & API actions will appear here."}
          </div>
        )}
      </div>
    </>
  );
}

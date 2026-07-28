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

const METHOD_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  GET:    { bg: "rgba(59,130,246,0.12)",  text: "#3b82f6",  border: "rgba(59,130,246,0.3)" },
  POST:   { bg: "rgba(34,197,94,0.12)",   text: "#22c55e",  border: "rgba(34,197,94,0.3)" },
  PUT:    { bg: "rgba(234,179,8,0.12)",   text: "#eab308",  border: "rgba(234,179,8,0.3)" },
  PATCH:  { bg: "rgba(249,115,22,0.12)",  text: "#f97316",  border: "rgba(249,115,22,0.3)" },
  DELETE: { bg: "rgba(239,68,68,0.12)",   text: "#ef4444",  border: "rgba(239,68,68,0.3)" },
};

function EntityCard({ entity }: { entity: Entity }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      className="rounded-lg overflow-hidden mb-2"
      style={{ border: "1px solid var(--border-color)" }}
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-3 py-2 text-left transition-colors"
        style={{ background: "var(--bg-card-hover)" }}
      >
        <div className="flex items-center gap-2">
          <Database className="w-3.5 h-3.5 shrink-0" style={{ color: "#a855f7" }} />
          <span className="font-medium text-sm" style={{ color: "var(--text-primary)" }}>
            {entity.name}
          </span>
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            ({entity.attributes.length} attrs)
          </span>
        </div>
        {open
          ? <ChevronDown className="w-3.5 h-3.5" style={{ color: "var(--text-muted)" }} />
          : <ChevronRight className="w-3.5 h-3.5" style={{ color: "var(--text-muted)" }} />
        }
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18 }}
            className="overflow-hidden"
          >
            {entity.description && (
              <p className="px-3 pt-2 text-xs italic" style={{ color: "var(--text-secondary)" }}>
                {entity.description}
              </p>
            )}
            <div className="px-3 py-2 space-y-1">
              {entity.attributes.map((attr) => (
                <div key={attr.name} className="flex items-center gap-2 text-xs">
                  <span className="font-mono" style={{ color: "var(--text-primary)" }}>{attr.name}</span>
                  <span className="font-mono" style={{ color: "#a855f7" }}>:{attr.data_type}</span>
                  {attr.is_required && (
                    <span className="text-[10px]" style={{ color: "#ef4444" }}>required</span>
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
    { key: "entities", label: "Entities", count: data?.entity_count ?? entities.length, icon: <Database className="w-3 h-3" />, color: "#a855f7" },
    { key: "relationships", label: "Relations", count: data?.relationship_count ?? relationships.length, icon: <Link2 className="w-3 h-3" />, color: "#3b82f6" },
    { key: "actions", label: "Actions", count: data?.action_count ?? actions.length, icon: <Zap className="w-3 h-3" />, color: "#eab308" },
  ];

  return (
    <>
      {/* Header */}
      <div
        className="px-3 py-3 border-b"
        style={{ borderColor: "var(--border-color)", background: "var(--bg-card)" }}
      >
        <div className="flex items-center gap-2 mb-2.5">
          <Database className="w-4 h-4" style={{ color: "#a855f7" }} />
          <h2 className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>
            Logic Extraction
            {data?.project_name && (
              <span className="ml-2 font-normal text-xs" style={{ color: "var(--text-muted)" }}>
                — {data.project_name}
              </span>
            )}
          </h2>
        </div>
        {/* Tabs */}
        <div className="flex gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-md border transition-all"
              style={
                activeTab === tab.key
                  ? { color: tab.color, borderColor: tab.color, background: `${tab.color}15` }
                  : { color: "var(--text-muted)", borderColor: "transparent", background: "transparent" }
              }
            >
              {tab.icon}
              {tab.label}
              {data && (
                <span className="font-bold text-[10px]">{tab.count}</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Body */}
      <div
        className="flex-1 p-3 overflow-auto"
        style={{ background: "var(--input-bg)" }}
      >
        {isProcessing && !data ? (
          <div className="flex items-center gap-2 text-sm" style={{ color: "#a855f7" }}>
            <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 2, ease: "linear" }}>
              <Code className="w-4 h-4" />
            </motion.div>
            <span>Extracting entities and domain model…</span>
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
                entities.length > 0
                  ? entities.map((e) => <EntityCard key={e.name} entity={e} />)
                  : <p className="text-xs" style={{ color: "var(--text-muted)" }}>No entities extracted.</p>
              )}

              {activeTab === "relationships" && (
                relationships.length > 0 ? (
                  <div className="space-y-2">
                    {relationships.map((r, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-2 text-xs rounded-lg px-3 py-2"
                        style={{ border: "1px solid var(--border-color)", background: "var(--bg-card-hover)" }}
                      >
                        <span className="font-medium" style={{ color: "#3b82f6" }}>{r.source}</span>
                        <span style={{ color: "var(--text-muted)" }}>— {r.relationship_type} →</span>
                        <span className="font-medium" style={{ color: "#3b82f6" }}>{r.target}</span>
                        {r.label && <span className="italic ml-auto" style={{ color: "var(--text-muted)" }}>{r.label}</span>}
                      </div>
                    ))}
                  </div>
                ) : <p className="text-xs" style={{ color: "var(--text-muted)" }}>No relationships extracted.</p>
              )}

              {activeTab === "actions" && (
                actions.length > 0 ? (
                  <div className="space-y-2">
                    {actions.map((a, i) => {
                      const mc = METHOD_COLORS[a.http_method] || { bg: "rgba(100,116,139,0.12)", text: "#64748b", border: "rgba(100,116,139,0.3)" };
                      return (
                        <div
                          key={i}
                          className="rounded-lg px-3 py-2 text-xs"
                          style={{ border: "1px solid var(--border-color)", background: "var(--bg-card-hover)" }}
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <span
                              className="px-1.5 py-0.5 rounded border font-bold font-mono text-[10px]"
                              style={{ background: mc.bg, color: mc.text, borderColor: mc.border }}
                            >
                              {a.http_method}
                            </span>
                            <span className="font-mono" style={{ color: "#eab308" }}>{a.endpoint}</span>
                          </div>
                          <div className="font-medium" style={{ color: "var(--text-primary)" }}>{a.name}</div>
                          {a.description && <div className="mt-0.5" style={{ color: "var(--text-secondary)" }}>{a.description}</div>}
                          {a.actor && <div className="mt-0.5" style={{ color: "var(--text-muted)" }}>Actor: {a.actor} → {a.target_entity}</div>}
                        </div>
                      );
                    })}
                  </div>
                ) : <p className="text-xs" style={{ color: "var(--text-muted)" }}>No actions extracted.</p>
              )}
            </motion.div>
          </AnimatePresence>
        ) : (
          <div className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
            {"// Upload an SRS and click Generate Architecture\n// Entities, relations, and API actions will appear here."}
          </div>
        )}
      </div>
    </>
  );
}

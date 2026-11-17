"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, ChevronRight, Database } from "lucide-react";
import { useState } from "react";
import type { Action, Entity, Relationship } from "@/types/api";

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

function EntityRow({ entity }: { entity: Entity }) {
  const [open, setOpen] = useState(false);
  return (
    <li style={{ borderBottom: "1px solid var(--rule)" }}>
      <button
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="w-full flex items-center gap-2 px-4 py-2.5 text-left transition-colors hover:bg-[var(--paper-2)]"
      >
        {open ? (
          <ChevronDown className="w-4 h-4 shrink-0" aria-hidden />
        ) : (
          <ChevronRight className="w-4 h-4 shrink-0" aria-hidden />
        )}
        <span className="font-semibold">{entity.name}</span>
        <span className="ml-auto text-sm tnum" style={{ color: "var(--ink-3)" }}>
          {entity.attributes.length} attrs
        </span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden"
          >
            {entity.description && (
              <p className="px-10 pb-2 text-sm" style={{ color: "var(--ink-2)" }}>
                {entity.description}
              </p>
            )}
            <table className="w-full text-sm font-mono mb-2">
              <tbody>
                {entity.attributes.map((attr, i) => (
                  <tr key={`${attr.name}-${i}`} style={{ borderTop: "1px solid var(--rule)" }}>
                    <td className="pl-10 pr-3 py-1">{attr.name}</td>
                    <td className="px-3 py-1" style={{ color: "var(--ink-2)" }}>
                      {attr.data_type}
                    </td>
                    <td className="pr-4 py-1 text-right" style={{ color: "var(--ink-3)" }}>
                      {attr.is_required ? "required" : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </motion.div>
        )}
      </AnimatePresence>
    </li>
  );
}

export default function ExtractionPanel({ isProcessing, data }: ExtractionPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>("entities");

  const entities = data?.entities || [];
  const relationships = data?.relationships || [];
  const actions = data?.actions || [];

  const tabs: { key: Tab; label: string; count: number }[] = [
    { key: "entities", label: "Entities", count: data?.entity_count ?? entities.length },
    { key: "relationships", label: "Relations", count: data?.relationship_count ?? relationships.length },
    { key: "actions", label: "Actions", count: data?.action_count ?? actions.length },
  ];

  return (
    <>
      <div className="panel-head">
        <Database className="w-4 h-4" aria-hidden />
        <h2 className="panel-title">
          Logic Extraction
          {data?.project_name && (
            <span className="font-normal ml-2" style={{ color: "var(--ink-3)" }}>
              {data.project_name}
            </span>
          )}
        </h2>
        <span className="zone-tag" aria-label="Zone C1">C1</span>
      </div>

      <div role="tablist" aria-label="Extraction" className="flex" style={{ borderBottom: "1px solid var(--rule)" }}>
        {tabs.map((tab) => {
          const active = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              role="tab"
              aria-selected={active}
              onClick={() => setActiveTab(tab.key)}
              className="relative px-4 py-2 text-sm font-semibold transition-colors hover:bg-[var(--paper-2)]"
              style={{ color: active ? "var(--ink)" : "var(--ink-3)" }}
            >
              {tab.label}
              {data && <span className="ml-1.5 tnum">{tab.count}</span>}
              {active && (
                <span
                  aria-hidden
                  className="absolute left-0 right-0 -bottom-px h-[3px]"
                  style={{ background: "var(--signal)" }}
                />
              )}
            </button>
          );
        })}
      </div>

      <div className="flex-1 min-h-0 overflow-auto">
        {isProcessing && !data ? (
          <div className="p-4 max-w-xs">
            <div className="stage" data-state="live">
              <div className="stage-bar">
                <span className="stage-chip" />
              </div>
              <span className="stage-label">Extracting entities and domain model…</span>
            </div>
          </div>
        ) : !data ? (
          <p className="p-4" style={{ color: "var(--ink-3)" }}>
            Entities, relationships and actions appear here after generation.
          </p>
        ) : (
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={activeTab}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.12 }}
            >
              {activeTab === "entities" &&
                (entities.length ? (
                  <ul>
                    {entities.map((e, i) => (
                      <EntityRow key={`${e.name}-${i}`} entity={e} />
                    ))}
                  </ul>
                ) : (
                  <p className="p-4" style={{ color: "var(--ink-3)" }}>No entities found.</p>
                ))}

              {activeTab === "relationships" &&
                (relationships.length ? (
                  <ul>
                    {relationships.map((r, i) => (
                      <li
                        key={i}
                        className="flex flex-wrap items-baseline gap-x-2 px-4 py-2.5"
                        style={{ borderBottom: "1px solid var(--rule)" }}
                      >
                        <span className="font-semibold">{r.source}</span>
                        <span aria-hidden style={{ color: "var(--signal)" }}>→</span>
                        <span className="font-semibold">{r.target}</span>
                        <span className="text-sm" style={{ color: "var(--ink-3)" }}>
                          {r.relationship_type}
                          {r.label ? ` · ${r.label}` : ""}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="p-4" style={{ color: "var(--ink-3)" }}>No relationships found.</p>
                ))}

              {activeTab === "actions" &&
                (actions.length ? (
                  <ul>
                    {actions.map((a, i) => (
                      <li
                        key={i}
                        className="flex items-baseline gap-3 px-4 py-2.5"
                        style={{ borderBottom: "1px solid var(--rule)" }}
                      >
                        <span
                          className="font-mono text-xs font-semibold px-1.5 py-0.5 border shrink-0 w-[3.9rem] text-center"
                          style={{ borderColor: "var(--ink)" }}
                        >
                          {a.http_method}
                        </span>
                        <span className="min-w-0">
                          <span className="block font-mono text-sm truncate">{a.endpoint}</span>
                          <span className="block text-sm" style={{ color: "var(--ink-2)" }}>
                            {a.name}
                            {a.actor ? <span style={{ color: "var(--ink-3)" }}> · {a.actor}</span> : null}
                          </span>
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="p-4" style={{ color: "var(--ink-3)" }}>No actions found.</p>
                ))}
            </motion.div>
          </AnimatePresence>
        )}
      </div>
    </>
  );
}

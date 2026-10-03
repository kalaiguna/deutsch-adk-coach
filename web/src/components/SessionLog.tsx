import { useState } from "react";
import type { Session } from "../lib/types";

const TYPE_BADGE: Record<string, string> = {
  conversation: "#8B5CF6", vocab: "#A78BFA", quiz: "#6366F1",
  reading: "#06B6D4", listening: "#0E7490", review: "#C084FC",
};

interface Props { sessions: Session[] }

export function SessionLog({ sessions }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div>
      <h3 style={{ fontSize: 15, fontWeight: 600, color: "#F8FAFC", marginBottom: 12 }}>Session Log</h3>
      <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 520, overflowY: "auto" }}>
        {sessions.length === 0 && <div style={{ color: "#64748B", fontSize: 13 }}>No sessions yet.</div>}
        {sessions.map(s => (
          <div key={s.id}>
            <div
              onClick={() => setExpanded(expanded === s.id ? null : s.id)}
              style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                padding: "10px 14px", borderRadius: 8, background: "#263448", cursor: "pointer",
                borderLeft: `3px solid ${TYPE_BADGE[s.type] ?? "#475569"}`,
              }}
            >
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: "#F8FAFC" }}>{s.name}</div>
                <div style={{ fontSize: 11, color: "#64748B", marginTop: 2 }}>{s.date}</div>
              </div>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <span style={{
                  fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 12, textTransform: "uppercase",
                  background: TYPE_BADGE[s.type] + "33", color: TYPE_BADGE[s.type] ?? "#94A3B8",
                }}>{s.type}</span>
                <span style={{ color: "#64748B", fontSize: 12 }}>{s.mistakes?.length ?? 0} mistakes</span>
                <span style={{ color: "#64748B", fontSize: 11 }}>{expanded === s.id ? "▲" : "▼"}</span>
              </div>
            </div>
            {expanded === s.id && (
              <div style={{ background: "#1E293B", padding: "12px 14px", borderRadius: "0 0 8px 8px", marginTop: 1 }}>
                {s.source_url && (
                  <a href={s.source_url} target="_blank" rel="noreferrer"
                    style={{ fontSize: 12, color: "#8B5CF6", display: "block", marginBottom: 8 }}>
                    {s.source_url}
                  </a>
                )}
                {(s.mistakes ?? []).length === 0 && (
                  <div style={{ fontSize: 12, color: "#64748B" }}>No mistakes recorded.</div>
                )}
                {(s.mistakes ?? []).map((m, i) => (
                  <div key={i} style={{ fontSize: 12, color: "#94A3B8", marginBottom: 4 }}>
                    <span style={{ color: "#F87171" }}>{m.original}</span>
                    {" → "}
                    <span style={{ color: "#34D399" }}>{m.correction}</span>
                    <span style={{ color: "#64748B" }}> [{m.category}]</span>
                  </div>
                ))}
                {(s.vocab_review_misses ?? []).length > 0 && (
                  <div style={{ marginTop: 8, fontSize: 12, color: "#94A3B8" }}>
                    Vocab misses: {s.vocab_review_misses.join(" · ")}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

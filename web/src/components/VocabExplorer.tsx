import { useState, useMemo } from "react";
import type { Session } from "../lib/types";

interface WordEntry { word: string; count: number; lastSeen: string }

interface Props { sessions: Session[] }

export function VocabExplorer({ sessions }: Props) {
  const [search, setSearch] = useState("");

  const words = useMemo<WordEntry[]>(() => {
    const map: Record<string, { count: number; lastSeen: string }> = {};
    for (const s of sessions) {
      for (const w of (s.vocab_review_misses ?? [])) {
        if (!map[w]) map[w] = { count: 0, lastSeen: s.date };
        map[w].count++;
        if (s.date > map[w].lastSeen) map[w].lastSeen = s.date;
      }
    }
    return Object.entries(map)
      .map(([word, v]) => ({ word, ...v }))
      .sort((a, b) => b.count - a.count);
  }, [sessions]);

  const cutoff30 = new Date(); cutoff30.setDate(cutoff30.getDate() - 30);
  const cutoffStr = cutoff30.toISOString().slice(0, 10);

  const filtered = words.filter(w => w.word.toLowerCase().includes(search.toLowerCase()));

  return (
    <div>
      <h3 style={{ fontSize: 15, fontWeight: 600, color: "#F8FAFC", marginBottom: 12 }}>Vocabulary Explorer</h3>
      <input
        placeholder="Search words..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        style={{
          width: "100%", padding: "8px 12px", borderRadius: 8, marginBottom: 12,
          background: "#263448", border: "1px solid #334155", color: "#F8FAFC",
          fontSize: 14, outline: "none",
        }}
      />
      <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 420, overflowY: "auto" }}>
        {filtered.length === 0 && (
          <div style={{ color: "#64748B", fontSize: 13 }}>No words found.</div>
        )}
        {filtered.map(w => {
          const stale = w.lastSeen < cutoffStr;
          return (
            <div key={w.word} style={{
              display: "flex", justifyContent: "space-between", alignItems: "center",
              padding: "8px 12px", borderRadius: 8, background: "#263448",
              borderLeft: `3px solid ${stale ? "#FB923C" : "#8B5CF6"}`,
            }}>
              <span style={{ fontSize: 14, color: stale ? "#FB923C" : "#F8FAFC", fontWeight: 500 }}>{w.word}</span>
              <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                <span style={{ fontSize: 11, color: "#64748B" }}>{w.lastSeen}</span>
                <span style={{
                  fontSize: 11, fontWeight: 700, padding: "2px 8px", borderRadius: 12,
                  background: w.count > 2 ? "#4C1D95" : "#2D1B69", color: "#C4B5FD",
                }}>×{w.count}</span>
              </div>
            </div>
          );
        })}
      </div>
      <div style={{ fontSize: 11, color: "#64748B", marginTop: 8 }}>
        {words.length} unique words · <span style={{ color: "#FB923C" }}>orange = not seen in 30+ days</span>
      </div>
    </div>
  );
}

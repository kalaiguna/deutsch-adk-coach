import type { Session } from "../lib/types";

interface Props { sessions: Session[] }

export function KpiTiles({ sessions }: Props) {
  const last30 = sessions.filter(s => {
    const cutoff = new Date(); cutoff.setDate(cutoff.getDate() - 30);
    return s.date >= cutoff.toISOString().slice(0, 10);
  });

  const totalSessions  = last30.length;
  const totalMistakes  = last30.reduce((n, s) => n + (s.mistakes?.length ?? 0), 0);
  const uniqueVocab    = new Set(last30.flatMap(s => s.vocab_review_misses ?? [])).size;
  const convSessions   = last30.filter(s => s.type === "conversation").length;

  const tiles = [
    { label: "Sessions (30d)",      value: totalSessions,  color: "#8B5CF6" },
    { label: "Mistakes logged",     value: totalMistakes,  color: "#F87171" },
    { label: "Unique vocab missed", value: uniqueVocab,    color: "#FB923C" },
    { label: "Conversation turns",  value: convSessions,   color: "#34D399" },
  ];

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16 }}>
      {tiles.map(t => (
        <div key={t.label} style={{
          background: "#1E293B", borderRadius: 12, padding: "20px 24px",
          borderLeft: `4px solid ${t.color}`,
        }}>
          <div style={{ fontSize: 28, fontWeight: 700, color: t.color }}>{t.value}</div>
          <div style={{ fontSize: 13, color: "#94A3B8", marginTop: 4 }}>{t.label}</div>
        </div>
      ))}
    </div>
  );
}

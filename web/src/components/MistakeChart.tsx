import type { Session, MistakeCategory } from "../lib/types";
import { ALL_CATEGORIES } from "../lib/types";

interface Props { sessions: Session[] }

export function MistakeChart({ sessions }: Props) {
  const counts: Record<string, number> = {};
  for (const cat of ALL_CATEGORIES) counts[cat] = 0;
  for (const s of sessions) {
    for (const m of (s.mistakes ?? [])) {
      if (counts[m.category] !== undefined) counts[m.category]++;
      else counts["Sonstiges"]++;
    }
  }

  const sorted = ALL_CATEGORIES
    .map(c => ({ cat: c as MistakeCategory, n: counts[c] }))
    .sort((a, b) => b.n - a.n);

  const max = Math.max(...sorted.map(x => x.n), 1);

  return (
    <div>
      <h3 style={{ fontSize: 15, fontWeight: 600, color: "#F8FAFC", marginBottom: 12 }}>Mistake Categories</h3>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {sorted.map(({ cat, n }) => (
          <div key={cat}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "#94A3B8", marginBottom: 3 }}>
              <span>{cat}</span><span>{n}</span>
            </div>
            <div style={{ height: 6, borderRadius: 3, background: "#263448" }}>
              <div style={{
                height: "100%", borderRadius: 3,
                width: `${(n / max) * 100}%`,
                background: n === 0 ? "#263448" : "#8B5CF6",
                transition: "width 0.4s ease",
              }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

import type { Session } from "../lib/types";

const TYPE_COLORS: Record<string, string> = {
  conversation: "#8B5CF6",
  vocab:        "#A78BFA",
  quiz:         "#6366F1",
  reading:      "#06B6D4",
  listening:    "#0E7490",
  review:       "#C084FC",
};

interface Props { sessions: Session[] }

export function ActivityHeatmap({ sessions }: Props) {
  // Build a date → types map for the last 52 weeks
  const byDate: Record<string, string[]> = {};
  for (const s of sessions) {
    if (!byDate[s.date]) byDate[s.date] = [];
    byDate[s.date].push(s.type);
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  // Align to Sunday
  const startDay = new Date(today);
  startDay.setDate(startDay.getDate() - startDay.getDay() - 52 * 7);

  const weeks: { date: string; types: string[] }[][] = [];
  let week: { date: string; types: string[] }[] = [];
  const cursor = new Date(startDay);

  while (cursor <= today) {
    const iso = cursor.toISOString().slice(0, 10);
    week.push({ date: iso, types: byDate[iso] ?? [] });
    if (cursor.getDay() === 6) { weeks.push(week); week = []; }
    cursor.setDate(cursor.getDate() + 1);
  }
  if (week.length) weeks.push(week);

  const cellColor = (types: string[]) => {
    if (!types.length) return "#263448";
    if (types.length === 1) return TYPE_COLORS[types[0]] ?? "#8B5CF6";
    return "#4C1D95"; // multiple types in one day
  };

  return (
    <div>
      <h3 style={{ fontSize: 15, fontWeight: 600, color: "#F8FAFC", marginBottom: 12 }}>Activity</h3>
      <div style={{ display: "flex", gap: 3, overflowX: "auto", paddingBottom: 4 }}>
        {weeks.map((w, wi) => (
          <div key={wi} style={{ display: "flex", flexDirection: "column", gap: 3 }}>
            {w.map(day => (
              <div
                key={day.date}
                title={day.date + (day.types.length ? ": " + day.types.join(", ") : "")}
                style={{
                  width: 12, height: 12, borderRadius: 2,
                  background: cellColor(day.types),
                  cursor: day.types.length ? "pointer" : "default",
                }}
              />
            ))}
          </div>
        ))}
      </div>
      <div style={{ display: "flex", gap: 12, marginTop: 8, flexWrap: "wrap" }}>
        {Object.entries(TYPE_COLORS).map(([type, color]) => (
          <div key={type} style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11, color: "#94A3B8" }}>
            <div style={{ width: 10, height: 10, borderRadius: 2, background: color }} />
            {type}
          </div>
        ))}
      </div>
    </div>
  );
}

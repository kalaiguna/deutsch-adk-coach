import { useState } from "react";
import { useSessions } from "./hooks/useSessions";
import { KpiTiles } from "./components/KpiTiles";
import { ActivityHeatmap } from "./components/ActivityHeatmap";
import { MistakeChart } from "./components/MistakeChart";
import { VocabExplorer } from "./components/VocabExplorer";
import { SessionLog } from "./components/SessionLog";
import { GespraechPanel } from "./components/GespraechPanel";

type NavSection = "overview" | "vocab" | "sessions" | "gespraech";

const NAV: { id: NavSection; label: string; icon: string }[] = [
  { id: "overview",   label: "Übersicht",  icon: "📊" },
  { id: "vocab",      label: "Vokabular",  icon: "📖" },
  { id: "sessions",   label: "Sitzungen",  icon: "🗓" },
  { id: "gespraech",  label: "Gespräch",   icon: "📞" },
];

export default function App() {
  const [section, setSection] = useState<NavSection>("overview");
  const { sessions, loading, error } = useSessions(90);

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0F172A", color: "#F8FAFC", fontFamily: "'Inter', sans-serif" }}>
      {/* Sidebar */}
      <aside style={{
        width: 220, flexShrink: 0, background: "#1E293B",
        borderRight: "1px solid #334155", display: "flex", flexDirection: "column",
        position: "sticky", top: 0, height: "100vh",
      }}>
        <div style={{ padding: "20px 16px 16px", borderBottom: "1px solid #334155" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 34, height: 34, background: "#8B5CF6", borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, fontWeight: 700 }}>D</div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700 }}>Deutsch Coach</div>
              <div style={{ fontSize: 11, color: "#94A3B8" }}>B2 Dashboard</div>
            </div>
          </div>
        </div>

        <nav style={{ padding: "12px 8px", flex: 1 }}>
          {NAV.map(n => (
            <button key={n.id} onClick={() => setSection(n.id)} style={{
              display: "flex", alignItems: "center", gap: 10,
              width: "100%", padding: "9px 12px", borderRadius: 8, border: "none",
              background: section === n.id ? "#2D1B69" : "transparent",
              color: section === n.id ? "#C4B5FD" : "#94A3B8",
              fontSize: 14, fontWeight: 500, cursor: "pointer", textAlign: "left",
              marginBottom: 2,
            }}>
              <span>{n.icon}</span>{n.label}
            </button>
          ))}
        </nav>

        <div style={{ padding: 16, borderTop: "1px solid #334155", fontSize: 11, color: "#475569" }}>
          {loading ? "Loading..." : error ? "Load error" : `${sessions.length} sessions`}
        </div>
      </aside>

      {/* Main content */}
      <main style={{ flex: 1, padding: 28, minWidth: 0 }}>
        {error && (
          <div style={{ background: "#3B1212", border: "1px solid #F87171", borderRadius: 8, padding: "10px 14px", marginBottom: 20, fontSize: 13, color: "#F87171" }}>
            Firestore error: {error}
          </div>
        )}

        {loading ? (
          <div style={{ color: "#64748B", fontSize: 14 }}>Loading sessions...</div>
        ) : (
          <>
            {section === "overview" && (
              <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                <h2 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>Übersicht</h2>
                <KpiTiles sessions={sessions} />
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                  <div style={{ background: "#1E293B", borderRadius: 12, padding: 20 }}>
                    <ActivityHeatmap sessions={sessions} />
                  </div>
                  <div style={{ background: "#1E293B", borderRadius: 12, padding: 20 }}>
                    <MistakeChart sessions={sessions} />
                  </div>
                </div>
              </div>
            )}

            {section === "vocab" && (
              <div>
                <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 20 }}>Vokabular</h2>
                <div style={{ background: "#1E293B", borderRadius: 12, padding: 20 }}>
                  <VocabExplorer sessions={sessions} />
                </div>
              </div>
            )}

            {section === "sessions" && (
              <div>
                <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 20 }}>Sitzungen</h2>
                <div style={{ background: "#1E293B", borderRadius: 12, padding: 20 }}>
                  <SessionLog sessions={sessions} />
                </div>
              </div>
            )}

            {section === "gespraech" && (
              <div>
                <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 20 }}>Gespräch</h2>
                <div style={{ background: "#1E293B", borderRadius: 12, padding: 20 }}>
                  <GespraechPanel />
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

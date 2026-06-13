import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import TriagePanel from "../components/TriagePanel";

type Card = { id: string; code: string; title: string; kind: string; body_md: string };

export default function Triage() {
  const [queue, setQueue] = useState<Card[] | null>(null);
  const [stats, setStats] = useState<any | null>(null);
  const [kind, setKind] = useState("source_card");

  async function refresh() {
    setQueue(await api.triageQueue(kind, 25));
    setStats(await api.triageStats(true));
  }

  useEffect(() => { refresh(); }, [kind]);

  if (!queue || !stats) return <div className="app"><div className="muted">Loading…</div></div>;

  return (
    <div className="app">
      <div className="header">
        <Link to="/library">← библиотека</Link>
        <span className="muted">Очередь триажа</span>
      </div>
      <h2>Триаж <span className="muted" style={{ fontSize: 14 }}>· {stats.total_verdicts} решений · {stats.extracted_organs} извлечённых органов</span></h2>

      <div className="card" style={{ marginTop: 8 }}>
        <div className="muted" style={{ fontSize: 12 }}>Что фильтровать:</div>
        <div style={{ display: "flex", gap: 8, marginTop: 6, flexWrap: "wrap" }}>
          {["source_card", "micro_game", "micro_aspect", "chimera", "residual"].map(k => (
            <button key={k} onClick={() => setKind(k)} style={{
              background: kind === k ? "rgba(80,160,80,0.25)" : "var(--bg)",
              border: kind === k ? "1px solid var(--accent)" : "1px solid var(--border)",
            }}>{k}</button>
          ))}
        </div>
        <div style={{ marginTop: 8, fontSize: 12, display: "flex", flexWrap: "wrap", gap: 8 }}>
          {stats.by_fate.map((f: any) => (
            <span key={f.fate} className="kbd">{f.label}: {f.count}</span>
          ))}
        </div>
      </div>

      {queue.length === 0 && (
        <div className="muted" style={{ marginTop: 16 }}>
          Ты прошёл всю очередь по этому типу. Переключи фильтр или вернись в библиотеку.
        </div>
      )}

      {queue.map(c => (
        <div key={c.id} className="card" style={{ marginTop: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
            <div>
              <span className="kbd">{c.code}</span> <b>{c.title}</b>
            </div>
            <Link to={`/library/entry/${c.id}`} className="muted" style={{ fontSize: 12 }}>открыть →</Link>
          </div>
          <div style={{ marginTop: 6, fontSize: 13, opacity: 0.9 }}>{c.body_md}</div>
          <TriagePanel entryId={c.id} onDone={refresh} />
        </div>
      ))}
    </div>
  );
}

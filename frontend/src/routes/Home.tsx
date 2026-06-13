import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { GameGenome } from "../types";

export default function Home() {
  const [games, setGames] = useState<GameGenome[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.listGames().then(setGames).catch(e => setErr(String(e)));
  }, []);

  return (
    <div className="app">
      <div className="header">
        <h1>Mindfield Games <span className="muted">— Operator Calibration Pack</span></h1>
        <div style={{ display: "flex", gap: 8 }}>
          <Link to="/library" className="kbd" style={{ textDecoration: "none" }}>Library →</Link>
          <Link to="/operator" className="kbd" style={{ textDecoration: "none" }}>Operator Profile →</Link>
        </div>
      </div>

      <p className="muted">
        Четыре micro-apps. Игрок действует по полю, LLM работает как назначенный орган сцены — прокурор, шпаклёвщик, адвокат ростка, буквальный чужой. После прохождения игр строится качественный Operator Profile, не числовой рейтинг.
      </p>

      {err && <div className="card" style={{ color: "var(--warn)" }}>API error: {err}</div>}

      {!games && !err && <div className="muted">Loading…</div>}

      {games && games.map(g => (
        <Link key={g.id} to={`/play/${g.id}`} style={{ textDecoration: "none", color: "inherit" }}>
          <div className="card game-card">
            <h3 style={{ margin: "0 0 4px" }}>{g.title}</h3>
            <div className="muted" style={{ fontSize: 13 }}>{g.function}</div>
          </div>
        </Link>
      ))}

      <div style={{ marginTop: 24, fontSize: 12, color: "var(--fg-dim)" }}>
        Не входит в MVP: auth, payments, multiplayer, RAG, marketplace, mobile app, Docker deploy. См. <code>docs/spec.md</code>.
      </div>
    </div>
  );
}

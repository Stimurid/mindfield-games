import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { GameSession } from "../types";

export default function Profile() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const nav = useNavigate();
  const [session, setSession] = useState<GameSession | null>(null);
  const [md, setMd] = useState<string>("");
  const [replaying, setReplaying] = useState(false);
  const [replayErr, setReplayErr] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    api.getSession(sessionId).then(setSession);
    api.exportMd(sessionId).then(setMd);
  }, [sessionId]);

  if (!session) return <div className="app"><div className="muted">Loading…</div></div>;
  const profile = session.trace_profile ?? {};

  async function startReplay() {
    if (!session) return;
    setReplaying(true);
    setReplayErr(null);
    try {
      const r = await api.replay(session.id);
      nav(`/play/${session.game_id}?materialId=${r.new_material_id}`);
    } catch (e: any) {
      setReplayErr(String(e?.message ?? e));
    } finally {
      setReplaying(false);
    }
  }

  function downloadMd() {
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `mindfield-${session?.id.slice(0, 8)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="app">
      <div className="header">
        <Link to="/">← все игры</Link>
        <button onClick={downloadMd}>Скачать .md</button>
      </div>
      <h2>Operator Profile <span className="muted" style={{ fontSize: 14 }}>· {session.game_id}</span></h2>
      <div className="card">
        <div className="muted" style={{ fontSize: 12 }}>Качественный профиль, не баллы. Замечаешь паттерн — следующий раунд бьёт по нему.</div>
        <div style={{ marginTop: 12 }}>
          {Object.entries(profile.dimensions ?? {}).map(([k, v]) => (
            <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--border)" }}>
              <span className="muted">{k}</span>
              <span><b>{typeof v === "object" ? JSON.stringify(v) : String(v)}</b></span>
            </div>
          ))}
        </div>
        {profile.replay_targets?.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <div className="muted" style={{ fontSize: 12 }}>Replay targets · теги для мутатора:</div>
            {profile.replay_targets.map((t: string) => <span key={t} className="kbd" style={{ marginRight: 6 }}>{t}</span>)}
          </div>
        )}
        {profile.replay_directives?.length > 0 && (
          <div style={{ marginTop: 16, padding: 12, background: "var(--bg)", borderRadius: 4, borderLeft: "3px solid var(--accent)" }}>
            <div className="muted" style={{ fontSize: 12, marginBottom: 6 }}>Что следующий раунд изменит конкретно:</div>
            {profile.replay_directives.map((d: string, i: number) => (
              <div key={i} style={{ marginTop: 4, fontSize: 13 }}>→ {d}</div>
            ))}
            <button
              className="primary"
              onClick={startReplay}
              disabled={replaying}
              style={{ marginTop: 12 }}
            >
              {replaying ? "Мутирую материал…" : "Сыграть мутировавший раунд"}
            </button>
            {replayErr && <div style={{ color: "var(--warn)", fontSize: 12, marginTop: 6 }}>{replayErr}</div>}
          </div>
        )}
      </div>
      <h3 style={{ marginTop: 24 }}>Markdown summary</h3>
      <pre className="profile">{md}</pre>
    </div>
  );
}

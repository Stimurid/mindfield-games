import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";

export default function Debug() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [data, setData] = useState<any | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    api.getSession(sessionId)
      .then(setData)
      .catch(e => setErr(String(e?.message ?? e)));
  }, [sessionId]);

  if (err) return <div className="app"><Link to="/">← все игры</Link><div className="card" style={{ color: "var(--warn)" }}>{err}</div></div>;
  if (!data) return <div className="app"><div className="muted">Loading…</div></div>;

  return (
    <div className="app">
      <div className="header">
        <Link to="/">← все игры</Link>
        <span className="muted">Debug session · raw JSON</span>
      </div>
      <h2>session {sessionId?.slice(0, 8)}</h2>
      <div className="card" style={{ marginTop: 8 }}>
        <div className="muted" style={{ fontSize: 12 }}>
          Полный объект сессии: moves, interventions, trace_profile. Для разработки и отладки.
        </div>
        <pre style={{ marginTop: 8, fontSize: 11, overflowX: "auto", whiteSpace: "pre-wrap" }}>
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    </div>
  );
}

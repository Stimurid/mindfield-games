import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useT } from "../i18n";

type Profile = Awaited<ReturnType<typeof api.getOperatorProfile>>;

const GAME_LABEL: Record<string, string> = {
  false_click: "False Click",
  missing_operation: "Missing Operation",
  sprout_or_slop: "Sprout or Slop",
  register_sapper: "Register Sapper",
};

export default function Operator() {
  const t = useT();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.getOperatorProfile().then(setProfile).catch(e => setErr(String(e?.message ?? e)));
  }, []);

  if (err) return <div className="app"><Link to="/">← {t("все игры", "all games")}</Link><div className="card" style={{ color: "var(--warn)" }}>{err}</div></div>;
  if (!profile) return <div className="app"><div className="muted">Loading…</div></div>;

  return (
    <div className="app">
      <div className="header">
        <Link to="/">← {t("все игры", "all games")}</Link>
      </div>

      <h2>Operator Profile <span className="muted" style={{ fontSize: 14 }}>· {t("сквозной портрет по жанрам", "cross-genre portrait")}</span></h2>

      <div className="card">
        <div className="muted" style={{ fontSize: 12 }}>{profile.coverage}</div>
        <div style={{ marginTop: 8, fontSize: 14 }}>{profile.verdict}</div>

        {profile.cross_patterns.length > 0 && (
          <div style={{ marginTop: 16, padding: 12, background: "var(--bg)", borderRadius: 4, borderLeft: "3px solid var(--accent)" }}>
            <div className="muted" style={{ fontSize: 12, marginBottom: 6 }}>{t("Связки между играми:", "Connections between games:")}</div>
            {profile.cross_patterns.map((p, i) => (
              <div key={i} style={{ marginTop: 6, fontSize: 13 }}>· {p}</div>
            ))}
          </div>
        )}

        {profile.explicit_dimensions.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <div className="muted" style={{ fontSize: 12, marginBottom: 6 }}>Поведенческие отметки по жанрам:</div>
            {profile.explicit_dimensions.map((d, i) => (
              <div key={i} style={{ marginTop: 4, fontSize: 13 }} dangerouslySetInnerHTML={{ __html: d.replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>") }} />
            ))}
          </div>
        )}
      </div>

      <h3 style={{ marginTop: 24 }}>{t("Сессии", "Sessions")}</h3>
      {profile.games_played.length === 0 && (
        <div className="muted">Ни одна игра ещё не пройдена. Начни с любой — потом сюда соберётся карта.</div>
      )}
      {profile.games_played.map(gid => {
        const g = profile.per_game[gid];
        return (
          <div key={gid} className="card" style={{ marginTop: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <strong>{GAME_LABEL[gid] ?? gid}</strong>
              <Link to={`/session/${g.session_id}/profile`} className="muted" style={{ fontSize: 12 }}>смотреть → </Link>
            </div>
            <div style={{ marginTop: 6 }}>
              {Object.entries(g.dimensions).map(([k, v]) => (
                <div key={k} style={{ fontSize: 12, marginTop: 2 }}>
                  <span className="muted">{k}</span> <b>{typeof v === "object" ? JSON.stringify(v) : String(v)}</b>
                </div>
              ))}
            </div>
            {g.replay_directives.length > 0 && (
              <div className="muted" style={{ fontSize: 11, marginTop: 6, fontStyle: "italic" }}>
                → {g.replay_directives[0]}
              </div>
            )}
          </div>
        );
      })}

      <div className="muted" style={{ fontSize: 11, marginTop: 24 }}>
        Профиль привязан к локальному токену в этом браузере. Очистка localStorage = новый игрок.
      </div>
    </div>
  );
}

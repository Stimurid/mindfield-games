import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";

type Question = { key: string; prompt: string; type: "yes_no" | "text" | "low_medium_high" };

export default function PlaytestFollowup() {
  const { token } = useParams<{ token: string }>();
  const [state, setState] = useState<any | null>(null);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api.followupGet(token)
      .then(s => {
        setState(s);
        const seed: Record<string, string> = {};
        for (const q of (s.checklist as Question[])) {
          const cur = s[q.key];
          if (cur) seed[q.key] = cur;
        }
        setDraft(seed);
        if (s.completed_at) setSubmitted(s.completed_at);
      })
      .catch(e => setErr(String(e?.message ?? e)));
  }, [token]);

  async function submit() {
    if (!token) return;
    setBusy(true);
    setErr(null);
    try {
      const r = await api.followupSubmit(token, draft);
      setSubmitted(r.submitted_at);
      const refreshed = await api.followupGet(token);
      setState(refreshed);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  if (err) return <div className="app"><div className="card" style={{ color: "var(--warn)" }}>{err}</div></div>;
  if (!state) return <div className="app"><div className="muted">Loading…</div></div>;

  const due = state.due_at ? new Date(state.due_at) : null;
  const now = new Date();
  const dueSoon = due && due.getTime() - now.getTime() < 0;

  return (
    <div className="app">
      <div className="header">
        <span className="muted">Mindfield · 24h follow-up</span>
      </div>
      <h2>Чек-лист переноса операции</h2>
      <p style={{ fontSize: 14 }}>
        Ты прошёл один полный цикл playtest около суток назад. Этот чек-лист собирает один
        важный сигнал: появилась ли операция, которую тренировала игра, ВНЕ приложения.
      </p>
      <div className="muted" style={{ fontSize: 12 }}>
        Создан: { state.run_completed_at ? new Date(state.run_completed_at).toLocaleString() : "—" } ·
        Срок: { due ? due.toLocaleString() : "—" }{dueSoon && submitted == null && " (просрочен — заполни всё равно)"}
      </div>

      {submitted && (
        <div className="card" style={{ marginTop: 12, borderLeft: "3px solid var(--accent)" }}>
          ✓ Ответы получены {new Date(submitted).toLocaleString()}.
          Ты можешь изменить ответы — они перезапишутся ниже.
        </div>
      )}

      {(state.checklist as Question[]).map(q => (
        <div key={q.key} className="card" style={{ marginTop: 8 }}>
          <div style={{ fontSize: 14 }}>{q.prompt}</div>
          <div style={{ marginTop: 6 }}>
            {q.type === "yes_no" && (
              <div style={{ display: "flex", gap: 6 }}>
                {["yes", "no", "unclear"].map(v => (
                  <button
                    key={v}
                    onClick={() => setDraft({ ...draft, [q.key]: v })}
                    style={{ background: draft[q.key] === v ? "rgba(80,160,80,0.25)" : "var(--bg)" }}
                  >
                    {v === "yes" ? "Да" : v === "no" ? "Нет" : "Не уверен"}
                  </button>
                ))}
              </div>
            )}
            {q.type === "low_medium_high" && (
              <div style={{ display: "flex", gap: 6 }}>
                {["low", "medium", "high"].map(v => (
                  <button
                    key={v}
                    onClick={() => setDraft({ ...draft, [q.key]: v })}
                    style={{ background: draft[q.key] === v ? "rgba(80,160,80,0.25)" : "var(--bg)" }}
                  >
                    {v === "low" ? "низкая" : v === "medium" ? "средняя" : "высокая"}
                  </button>
                ))}
              </div>
            )}
            {q.type === "text" && (
              <textarea
                value={draft[q.key] ?? ""}
                onChange={e => setDraft({ ...draft, [q.key]: e.target.value })}
                placeholder="ответь в одно-два предложения"
                style={{ width: "100%", minHeight: 60 }}
              />
            )}
          </div>
        </div>
      ))}

      <div className="actions-bar" style={{ marginTop: 12 }}>
        <button className="primary" onClick={submit} disabled={busy}>
          {busy ? "Отправляю…" : submitted ? "Перезаписать ответы" : "Отправить"}
        </button>
      </div>
    </div>
  );
}

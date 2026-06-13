import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";

const ROLE_LABEL: Record<string, string> = {
  prosecutor: "Атаковать прокурором",
  spackler: "Заштукатурить",
  sprout_advocate: "Защитить как росток",
  literal_alien: "Прочитать буквально",
};

export default function ResearchHypothesis() {
  const { id } = useParams<{ id: string }>();
  const isNew = !id || id === "new";
  const nav = useNavigate();

  const [h, setH] = useState<any | null>(isNew ? { title: "", body_md: "", tags: [], status: "draft" } : null);
  const [discussions, setDiscussions] = useState<any[]>([]);
  const [drafts, setDrafts] = useState<any[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (isNew) return;
    api.researchGetHypothesis(id!).then(setH).catch(e => setErr(String(e?.message ?? e)));
    api.researchDiscussions(id!).then(setDiscussions).catch(() => {});
    api.configListDrafts(true).then(setDrafts).catch(() => {});
  }, [id]);

  async function save() {
    setBusy("save");
    setErr(null);
    try {
      if (isNew) {
        const created = await api.researchCreateHypothesis({
          title: h.title || "untitled",
          body_md: h.body_md,
          tags: h.tags ?? [],
          linked_draft_id: h.linked_draft_id ?? null,
        });
        nav(`/research/hypotheses/${created.id}`);
      } else {
        const updated = await api.researchPatchHypothesis(id!, {
          title: h.title,
          body_md: h.body_md,
          tags: h.tags,
          status: h.status,
          linked_draft_id: h.linked_draft_id,
        });
        setH(updated);
      }
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally { setBusy(null); }
  }

  async function summon(role: string) {
    if (!id) return;
    setBusy(role);
    setErr(null);
    try {
      const c = await api.researchSummon(id, role);
      setDiscussions([c, ...discussions]);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally { setBusy(null); }
  }

  async function destroy() {
    if (!id) return;
    if (!confirm("Удалить гипотезу? Дискуссия пропадёт.")) return;
    await api.researchDeleteHypothesis(id);
    nav("/research");
  }

  if (!h) return <div className="app"><div className="muted">Loading…</div></div>;

  return (
    <div className="app">
      <div className="header" style={{ flexWrap: "wrap", gap: 8 }}>
        <Link to="/research">← гипотезы</Link>
        {!isNew && h.id && <span className="muted" style={{ fontSize: 11 }}>{h.id.slice(0, 8)}</span>}
      </div>

      <div className="card">
        <input
          value={h.title}
          onChange={e => setH({ ...h, title: e.target.value })}
          placeholder="Заголовок гипотезы"
          style={{ width: "100%", fontSize: 16, fontWeight: "bold" }}
        />
        <textarea
          value={h.body_md ?? ""}
          onChange={e => setH({ ...h, body_md: e.target.value })}
          placeholder="Тело гипотезы. Что ты утверждаешь? Что для тебя стало бы свидетельством против?"
          style={{ marginTop: 8, minHeight: 180, fontFamily: "monospace", width: "100%" }}
        />
        <div style={{ marginTop: 8, display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          {!isNew && (
            <>
              <label className="muted" style={{ fontSize: 12 }}>статус:</label>
              <select value={h.status} onChange={e => setH({ ...h, status: e.target.value })}>
                <option value="draft">draft</option>
                <option value="published">published</option>
                <option value="abandoned">abandoned</option>
              </select>
            </>
          )}
          <label className="muted" style={{ fontSize: 12, marginLeft: 8 }}>привязать к черновику:</label>
          <select
            value={h.linked_draft_id ?? ""}
            onChange={e => setH({ ...h, linked_draft_id: e.target.value || null })}
          >
            <option value="">— не привязана</option>
            {drafts.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
        </div>
        <div className="actions-bar" style={{ marginTop: 12 }}>
          <button className="primary" onClick={save} disabled={busy === "save"}>
            {busy === "save" ? "Сохраняю…" : (isNew ? "Создать" : "Сохранить")}
          </button>
          {!isNew && <button onClick={destroy} style={{ color: "var(--warn)" }}>Удалить</button>}
          {h.linked_draft_id && <Link to="/configurator" className="kbd" style={{ textDecoration: "none" }}>→ конфигуратор</Link>}
        </div>
        {err && <div style={{ color: "var(--warn)", fontSize: 12, marginTop: 6 }}>{err}</div>}
      </div>

      {!isNew && (
        <>
          <div className="card" style={{ marginTop: 12 }}>
            <div className="muted" style={{ fontSize: 12, marginBottom: 8 }}>
              Вызвать орган над гипотезой. Один клик = один ход роли. Это не чат.
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {(["prosecutor", "spackler", "sprout_advocate", "literal_alien"] as const).map(r => (
                <button key={r} onClick={() => summon(r)} disabled={busy !== null}>
                  {busy === r ? "Вызываю…" : ROLE_LABEL[r]}
                </button>
              ))}
            </div>
          </div>

          {discussions.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <div className="muted" style={{ fontSize: 12, marginBottom: 6 }}>
                Зафиксированные ходы органов ({discussions.length}):
              </div>
              {discussions.map(c => (
                <div key={c.id} className="card" style={{ marginTop: 8, fontSize: 13 }}>
                  <div className="llm-role-tag" style={{ display: "inline-block" }}>{c.role}</div>
                  <span className="muted" style={{ marginLeft: 8, fontSize: 11 }}>{c.model ?? ""} · {c.created_at?.slice(0, 19)}</span>
                  <div style={{ marginTop: 6 }}>
                    {Object.entries(c.output ?? {}).map(([k, v]) => (
                      <div key={k} style={{ marginTop: 3 }}>
                        <b>{k}:</b>{" "}
                        {Array.isArray(v)
                          ? <ul style={{ margin: "4px 0 0 16px" }}>{(v as string[]).map((x, i) => <li key={i}>{x}</li>)}</ul>
                          : String(v)}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="muted" style={{ fontSize: 11, marginTop: 12, fontStyle: "italic" }}>
            Поделиться: скопируй URL этой страницы. У получателя свой player_token, но запись и
            история органов открыты по UUID.
          </div>
        </>
      )}
    </div>
  );
}

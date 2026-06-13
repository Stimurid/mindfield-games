import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useT } from "../i18n";

type Bank = { bank: string; label: string; hint: string; count: number; is_degradation: boolean };
type Organ = { id: string; bank: string; name: string };
type Verdict = {
  verb_status: string;
  crisis_status: string;
  trace_status: string;
  degradation_warnings: string[];
  playable_verdict: string;
  critique: string;
};

const STAGE_LABEL = ["0 сырой фрагмент", "1 упражнение", "2 игра-упражнение", "3 психотехническая игра", "4 коэволюционный симулятор", "5 школа/платформа"];

export default function Configurator() {
  const t = useT();
  const nav = useNavigate();
  const [fieldTypes, setFieldTypes] = useState<{ id: string; label: string }[]>([]);
  const [promoteFieldType, setPromoteFieldType] = useState<string>("clickable_text_units");
  const [banks, setBanks] = useState<Bank[] | null>(null);
  const [organsByBank, setOrgansByBank] = useState<Record<string, Organ[]>>({});
  const [name, setName] = useState("");
  const [fn, setFn] = useState("");
  const [verb, setVerb] = useState("");
  const [stage, setStage] = useState(1);
  const [selected, setSelected] = useState<Record<string, Set<string>>>({});
  const [drafts, setDrafts] = useState<any[]>([]);
  const [currentDraftId, setCurrentDraftId] = useState<string | null>(null);
  const [verdict, setVerdict] = useState<Verdict | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.configBanks().then(async bs => {
      setBanks(bs);
      const map: Record<string, Organ[]> = {};
      for (const b of bs) {
        map[b.bank] = await api.configOrgans(b.bank);
      }
      setOrgansByBank(map);
    }).catch(e => setErr(String(e?.message ?? e)));
    api.configListDrafts(true).then(setDrafts).catch(() => {});
    api.configListFieldTypes().then(setFieldTypes).catch(() => {});
  }, []);

  function toggle(bank: string, organId: string) {
    const cur = new Set(selected[bank] ?? []);
    if (cur.has(organId)) cur.delete(organId);
    else cur.add(organId);
    setSelected({ ...selected, [bank]: cur });
  }

  function selectedAsRecord(): Record<string, string[]> {
    const out: Record<string, string[]> = {};
    for (const [bank, s] of Object.entries(selected)) {
      const arr = Array.from(s);
      if (arr.length) out[bank] = arr;
    }
    return out;
  }

  async function saveDraft() {
    setBusy(true);
    setErr(null);
    try {
      const payload = {
        name: name.trim() || "untitled draft",
        function: fn.trim() || undefined,
        verb: verb.trim() || undefined,
        maturity_stage: stage,
        selected_organs: selectedAsRecord(),
      };
      let d;
      if (currentDraftId) {
        d = await api.configPatchDraft(currentDraftId, payload);
      } else {
        d = await api.configCreateDraft(payload);
        setCurrentDraftId(d.id);
      }
      setDrafts(await api.configListDrafts(true));
      setVerdict(d.weaver_verdict ?? null);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  async function promote() {
    if (!currentDraftId) {
      await saveDraft();
      if (!currentDraftId) return;
    }
    setBusy(true);
    setErr(null);
    try {
      const r = await api.configPromoteDraft(currentDraftId!, promoteFieldType);
      nav(`/play/${r.promoted_game_id}`);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  async function runWeaver() {
    if (!currentDraftId) {
      await saveDraft();
      if (!currentDraftId) return;
    }
    setBusy(true);
    setErr(null);
    try {
      const id = currentDraftId!;
      // Ensure latest is on the server before validating.
      await api.configPatchDraft(id, {
        name: name.trim() || "untitled draft",
        function: fn.trim() || undefined,
        verb: verb.trim() || undefined,
        maturity_stage: stage,
        selected_organs: selectedAsRecord(),
      });
      const r = await api.configRunWeaver(id);
      setVerdict(r.verdict);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  async function loadDraft(d: any) {
    setCurrentDraftId(d.id);
    setName(d.name);
    setFn(d.function ?? "");
    setVerb(d.verb ?? "");
    setStage(d.maturity_stage ?? 1);
    const sel: Record<string, Set<string>> = {};
    for (const [bank, ids] of Object.entries(d.selected_organs ?? {})) {
      sel[bank] = new Set(ids as string[]);
    }
    setSelected(sel);
    setVerdict(d.weaver_verdict ?? null);
  }

  function resetForm() {
    setCurrentDraftId(null);
    setName(""); setFn(""); setVerb(""); setStage(1);
    setSelected({}); setVerdict(null);
  }

  if (!banks) return <div className="app"><div className="muted">Loading…</div></div>;

  return (
    <div className="app">
      <div className="header">
        <Link to="/">← {t("все игры", "all games")}</Link>
        <span className="muted">{t("Конфигуратор · GameWeaver", "Configurator · GameWeaver")}</span>
      </div>

      <h2>Configurator</h2>
      <p className="muted" style={{ fontSize: 13 }}>
        Собери черновик игры из 8 банков органов. GameWeaver — это критик играбельности, не помощник;
        он валит черновик, если нет глагола, нет кризиса, нет следа, или выбран орган деградации.
      </p>

      {err && <div className="card" style={{ color: "var(--warn)" }}>{err}</div>}

      <div className="card" style={{ marginTop: 12 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          <div>
            <label className="muted" style={{ fontSize: 12 }}>имя черновика</label>
            <input value={name} onChange={e => setName(e.target.value)} placeholder="например, Игра под захватом" />
          </div>
          <div>
            <label className="muted" style={{ fontSize: 12 }}>родовая функция</label>
            <input value={fn} onChange={e => setFn(e.target.value)} placeholder="что у игрока должно сформироваться" />
          </div>
          <div>
            <label className="muted" style={{ fontSize: 12 }}>playable verb</label>
            <input value={verb} onChange={e => setVerb(e.target.value)} placeholder="кликнуть / молчать / похоронить…" />
          </div>
          <div>
            <label className="muted" style={{ fontSize: 12 }}>стадия зрелости</label>
            <select value={stage} onChange={e => setStage(parseInt(e.target.value))}>
              {STAGE_LABEL.map((s, i) => <option key={i} value={i}>{s}</option>)}
            </select>
          </div>
        </div>
      </div>

      {banks.map(b => {
        const list = organsByBank[b.bank] ?? [];
        const sel = selected[b.bank] ?? new Set<string>();
        return (
          <div
            key={b.bank}
            className="card"
            style={{
              marginTop: 12,
              borderLeft: b.is_degradation ? "3px solid var(--warn)" : undefined,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <strong>{b.label}</strong>
                <span className="muted" style={{ fontSize: 12, marginLeft: 8 }}>{b.hint}</span>
              </div>
              <span className="kbd">{sel.size} / {b.count}</span>
            </div>
            <div style={{ marginTop: 8, display: "flex", flexWrap: "wrap", gap: 6 }}>
              {list.map(o => {
                const on = sel.has(o.id);
                return (
                  <button
                    key={o.id}
                    onClick={() => toggle(b.bank, o.id)}
                    style={{
                      fontSize: 12, padding: "4px 8px",
                      background: on
                        ? (b.is_degradation ? "rgba(220,160,0,0.25)" : "rgba(80,160,80,0.25)")
                        : "var(--bg)",
                      border: on ? "1px solid var(--accent)" : "1px solid var(--border)",
                    }}
                  >
                    {o.name}
                  </button>
                );
              })}
            </div>
          </div>
        );
      })}

      <div className="actions-bar" style={{ marginTop: 12, flexWrap: "wrap" }}>
        <button onClick={saveDraft} disabled={busy}>{currentDraftId ? t("Сохранить", "Save") : t("Создать черновик", "Create draft")}</button>
        <button className="primary" onClick={runWeaver} disabled={busy}>{busy ? t("GameWeaver работает…", "GameWeaver running…") : t("Прогнать через GameWeaver", "Run GameWeaver")}</button>
        {currentDraftId && <button onClick={resetForm}>{t("Новый", "New")}</button>}
        {currentDraftId && (
          <span style={{ display: "flex", gap: 6, alignItems: "center", marginLeft: 12 }}>
            <span className="muted" style={{ fontSize: 12 }}>{t("промотировать как:", "promote as:")}</span>
            <select value={promoteFieldType} onChange={e => setPromoteFieldType(e.target.value)}>
              {fieldTypes.map(ft => <option key={ft.id} value={ft.id}>{ft.label}</option>)}
            </select>
            <button onClick={promote} disabled={busy} style={{ background: "rgba(80,160,80,0.25)" }}>
              {t("Промотировать и сыграть", "Promote and play")}
            </button>
          </span>
        )}
      </div>

      {verdict && (
        <div
          className="card"
          style={{
            marginTop: 12,
            borderLeft: `3px solid ${
              verdict.playable_verdict === "playable" ? "var(--accent)" :
              verdict.playable_verdict === "rotten" ? "var(--warn)" :
              "var(--fg-dim)"
            }`,
          }}
        >
          <div className="llm-role-tag">playability_critic · GameWeaver</div>
          <div style={{ marginTop: 8, fontSize: 14 }}>{verdict.critique}</div>
          <div style={{ marginTop: 8, fontSize: 12 }}>
            <span className="muted">verb:</span> <b>{verdict.verb_status}</b>{" "}
            <span className="muted">crisis:</span> <b>{verdict.crisis_status}</b>{" "}
            <span className="muted">trace:</span> <b>{verdict.trace_status}</b>{" "}
            <span className="muted">verdict:</span> <b>{verdict.playable_verdict}</b>
          </div>
          {verdict.degradation_warnings.length > 0 && (
            <div style={{ marginTop: 6, fontSize: 12, color: "var(--warn)" }}>
              ⚠ органы деградации: {verdict.degradation_warnings.join(", ")}
            </div>
          )}
        </div>
      )}

      <h3 style={{ marginTop: 24 }}>Мои черновики</h3>
      {drafts.length === 0 && <div className="muted">пусто — создай первый</div>}
      {drafts.map(d => (
        <div key={d.id} className="card" style={{ marginTop: 8, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <b>{d.name}</b>{" "}
            <span className="muted" style={{ fontSize: 12 }}>verb={d.verb ?? "—"} · stage={d.maturity_stage}</span>
            {d.weaver_verdict && (
              <span className="kbd" style={{ marginLeft: 8 }}>
                {d.weaver_verdict.playable_verdict}
              </span>
            )}
          </div>
          <button onClick={() => loadDraft(d)}>Открыть</button>
        </div>
      ))}
    </div>
  );
}

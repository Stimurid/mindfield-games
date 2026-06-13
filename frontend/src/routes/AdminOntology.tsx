import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useT } from "../i18n";

const BANKS = ["field", "object", "action", "llm_role", "crisis", "trace", "mutation", "degradation"] as const;

export default function AdminOntology() {
  const t = useT();
  const [organs, setOrgans] = useState<any[]>([]);
  const [fates, setFates] = useState<any | null>(null);
  const [patterns, setPatterns] = useState<any | null>(null);
  const [bankFilter, setBankFilter] = useState<string>("");
  const [draft, setDraft] = useState({ bank: "action", name: "", description: "" });
  const [editing, setEditing] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState<any>({});
  const [err, setErr] = useState<string | null>(null);

  async function refresh() {
    setOrgans(await api.adminListOrgans(bankFilter || undefined));
  }

  useEffect(() => { refresh(); }, [bankFilter]);
  useEffect(() => {
    api.adminOntologyFates().then(setFates).catch(() => {});
    api.adminOntologyCrossPatterns().then(setPatterns).catch(() => {});
  }, []);

  async function create() {
    setErr(null);
    try {
      await api.adminCreateOrgan(draft);
      setDraft({ bank: draft.bank, name: "", description: "" });
      await refresh();
    } catch (e: any) { setErr(String(e?.message ?? e)); }
  }

  async function saveEdit(id: string) {
    setErr(null);
    try {
      await api.adminUpdateOrgan(id, editDraft);
      setEditing(null);
      await refresh();
    } catch (e: any) { setErr(String(e?.message ?? e)); }
  }

  async function delOrgan(id: string) {
    setErr(null);
    if (!confirm(t("Удалить орган?", "Delete organ?"))) return;
    try {
      await api.adminDeleteOrgan(id);
      await refresh();
    } catch (e: any) { setErr(String(e?.message ?? e)); }
  }

  return (
    <div className="app">
      <div className="header">
        <Link to="/">← {t("все игры", "all games")}</Link>
        <span className="muted">{t("Admin · Онтология", "Admin · Ontology")}</span>
      </div>
      <h2>{t("Онтология сборки", "Assembly ontology")}</h2>
      <p className="muted" style={{ fontSize: 12 }}>
        {t(
          "Канонические органы из spec.md §8 — read-only (защищены от удаления). Можно добавлять свои в любой банк (source=admin_authored). Словарь судеб триажа и связки профиля сейчас определяются в коде.",
          "Canonical organs from spec.md §8 are read-only (protected from deletion). You can add your own organs to any bank (source=admin_authored). The triage fate vocabulary and profile cross-patterns are currently code-defined.",
        )}
      </p>

      {err && <div className="card" style={{ color: "var(--warn)" }}>{err}</div>}

      <h3 style={{ marginTop: 24 }}>{t("Органы", "Organs")} <span className="muted" style={{ fontSize: 13, fontWeight: "normal" }}>· {organs.length}</span></h3>

      <div className="card" style={{ marginTop: 8 }}>
        <div className="muted" style={{ fontSize: 12 }}>{t("Создать новый орган", "Create new organ")}</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr 2fr", gap: 6, marginTop: 6 }}>
          <select value={draft.bank} onChange={e => setDraft({ ...draft, bank: e.target.value })}>
            {BANKS.map(b => <option key={b} value={b}>{b}</option>)}
          </select>
          <input placeholder={t("имя органа", "organ name")} value={draft.name}
                 onChange={e => setDraft({ ...draft, name: e.target.value })} />
          <input placeholder={t("описание (опционально)", "description (optional)")} value={draft.description}
                 onChange={e => setDraft({ ...draft, description: e.target.value })} />
        </div>
        <div className="actions-bar" style={{ marginTop: 6 }}>
          <button className="primary" onClick={create} disabled={!draft.name.trim()}>
            {t("Добавить", "Add")}
          </button>
        </div>
      </div>

      <div style={{ marginTop: 12 }}>
        <span className="muted" style={{ fontSize: 12 }}>{t("Фильтр по банку:", "Filter by bank:")} </span>
        <select value={bankFilter} onChange={e => setBankFilter(e.target.value)}>
          <option value="">{t("все", "all")}</option>
          {BANKS.map(b => <option key={b} value={b}>{b}</option>)}
        </select>
      </div>

      {organs.map(o => (
        <div key={o.id} className="card" style={{ marginTop: 6, fontSize: 13,
              borderLeft: o.source === "canon_v0.1" ? "3px solid var(--accent)" :
                          o.bank === "degradation" ? "3px solid var(--warn)" : undefined }}>
          {editing === o.id ? (
            <div>
              <input value={editDraft.name ?? o.name}
                     onChange={e => setEditDraft({ ...editDraft, name: e.target.value })} />
              <input value={editDraft.description ?? o.description ?? ""}
                     style={{ marginTop: 4 }}
                     onChange={e => setEditDraft({ ...editDraft, description: e.target.value })} />
              <div className="actions-bar" style={{ marginTop: 6 }}>
                <button className="primary" onClick={() => saveEdit(o.id)}>{t("Сохранить", "Save")}</button>
                <button onClick={() => setEditing(null)}>{t("Отмена", "Cancel")}</button>
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ flex: 1 }}>
                <span className="kbd" style={{ marginRight: 6 }}>{o.bank}</span>
                <span className="kbd" style={{ marginRight: 6, opacity: 0.6 }}>{o.source}</span>
                <b>{o.name}</b>
                {o.description && <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>{o.description}</div>}
              </div>
              {o.source !== "canon_v0.1" && (
                <div style={{ display: "flex", gap: 4 }}>
                  <button onClick={() => { setEditing(o.id); setEditDraft({}); }}>Edit</button>
                  <button onClick={() => delOrgan(o.id)} style={{ color: "var(--warn)" }}>Del</button>
                </div>
              )}
            </div>
          )}
        </div>
      ))}

      <h3 style={{ marginTop: 32 }}>{t("Судьбы триажа", "Triage fates")} <span className="kbd" style={{ marginLeft: 8, fontSize: 11 }}>code-defined</span></h3>
      {fates && (
        <div className="card" style={{ marginTop: 8 }}>
          <div className="muted" style={{ fontSize: 12 }}>
            {t("Определены в", "Defined in")}: <code>{fates.source_file}</code>
          </div>
          <ul style={{ marginTop: 8 }}>
            {fates.fates.map((f: any) => (
              <li key={f.fate}><code>{f.fate}</code> — {f.label}</li>
            ))}
          </ul>
        </div>
      )}

      <h3 style={{ marginTop: 32 }}>{t("Cross-patterns профиля", "Profile cross-patterns")} <span className="kbd" style={{ marginLeft: 8, fontSize: 11 }}>code-defined</span></h3>
      {patterns && (
        <>
          <div className="card" style={{ marginTop: 8 }}>
            <div className="muted" style={{ fontSize: 12 }}>
              {t("Определены в", "Defined in")}: <code>{patterns.source_file}</code>
            </div>
            <ul style={{ marginTop: 8 }}>
              {patterns.patterns.map((p: any, i: number) => (
                <li key={i}>
                  {p.name}
                  <div className="muted" style={{ fontSize: 11, marginLeft: 16 }}>
                    {t("нужно", "needs")}: {p.needed_dimensions.map((d: any) => `${d.game_id}=${d.value}`).join(" + ")}
                  </div>
                </li>
              ))}
            </ul>
          </div>
          <h4 style={{ marginTop: 16 }}>{t("Словарь значений размерностей", "Dimension value vocabulary")}</h4>
          <div className="card" style={{ marginTop: 8, fontSize: 12 }}>
            {patterns.bias_meanings.map((m: any, i: number) => (
              <div key={i} style={{ marginTop: 4 }}>
                <code>{m.game_id}.{m.value}</code> — {m.meaning}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

type Mat = {
  id: string;
  game_id: string;
  title: string;
  namespace: string;
  payload: any;
  parent_id?: string | null;
  source_corpus_id?: string | null;
  mutation_directive?: string | null;
  created_at?: string | null;
};

export default function Admin() {
  const [rows, setRows] = useState<Mat[] | null>(null);
  const [editing, setEditing] = useState<Mat | null>(null);
  const [draft, setDraft] = useState<{ game_id: string; title: string; namespace: string; payload: string }>({
    game_id: "false_click", title: "", namespace: "demo", payload: "{}",
  });
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    setRows(await api.adminListMaterials());
  }

  useEffect(() => { refresh(); }, []);

  async function create() {
    setBusy(true);
    setErr(null);
    try {
      const payload = JSON.parse(draft.payload);
      await api.adminCreateMaterial({ ...draft, payload });
      setDraft({ ...draft, title: "", payload: "{}" });
      await refresh();
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally { setBusy(false); }
  }

  async function save() {
    if (!editing) return;
    setBusy(true);
    setErr(null);
    try {
      await api.adminUpdateMaterial(editing.id, {
        title: editing.title,
        namespace: editing.namespace,
        payload: editing.payload,
      });
      setEditing(null);
      await refresh();
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally { setBusy(false); }
  }

  async function del(id: string) {
    if (!confirm("Удалить материал? Действие необратимо.")) return;
    await api.adminDeleteMaterial(id);
    await refresh();
  }

  return (
    <div className="app">
      <div className="header">
        <Link to="/">← все игры</Link>
        <span className="muted">Admin · CRUD материалов</span>
      </div>
      <h2>Admin / Materials</h2>
      <p className="muted" style={{ fontSize: 12 }}>
        Прямой редактор материалов. Авторизации нет — продакшн защищён basic_auth Caddy.
      </p>

      {err && <div className="card" style={{ color: "var(--warn)" }}>{err}</div>}

      <div className="card" style={{ marginTop: 12 }}>
        <div className="muted" style={{ fontSize: 12 }}>Создать новый материал</div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr 1fr", gap: 6, marginTop: 6 }}>
          <input placeholder="game_id" value={draft.game_id} onChange={e => setDraft({ ...draft, game_id: e.target.value })} />
          <input placeholder="title" value={draft.title} onChange={e => setDraft({ ...draft, title: e.target.value })} />
          <input placeholder="namespace (demo|real)" value={draft.namespace} onChange={e => setDraft({ ...draft, namespace: e.target.value })} />
        </div>
        <textarea
          placeholder='payload (JSON, e.g. {"type":"clickable_text_units","intro":"...","units":[...]})'
          value={draft.payload}
          onChange={e => setDraft({ ...draft, payload: e.target.value })}
          style={{ marginTop: 6, minHeight: 120, fontFamily: "monospace", width: "100%" }}
        />
        <div className="actions-bar" style={{ marginTop: 6 }}>
          <button className="primary" onClick={create} disabled={busy}>Создать</button>
        </div>
      </div>

      <h3 style={{ marginTop: 24 }}>Существующие материалы ({rows?.length ?? "…"})</h3>
      {rows?.map(m => (
        <div key={m.id} className="card" style={{ marginTop: 8 }}>
          {editing?.id === m.id ? (
            <div>
              <input value={editing.title} onChange={e => setEditing({ ...editing, title: e.target.value })} />
              <input value={editing.namespace} onChange={e => setEditing({ ...editing, namespace: e.target.value })} style={{ marginTop: 6 }} />
              <textarea
                value={JSON.stringify(editing.payload, null, 2)}
                onChange={e => {
                  try { setEditing({ ...editing, payload: JSON.parse(e.target.value) }); } catch {}
                }}
                style={{ marginTop: 6, minHeight: 180, fontFamily: "monospace", width: "100%" }}
              />
              <div className="actions-bar" style={{ marginTop: 6 }}>
                <button className="primary" onClick={save} disabled={busy}>Сохранить</button>
                <button onClick={() => setEditing(null)}>Отмена</button>
              </div>
            </div>
          ) : (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 4 }}>
                <div>
                  <span className="kbd">{m.namespace}</span>{" "}
                  <span className="kbd">{m.game_id}</span>{" "}
                  <b>{m.title}</b>
                </div>
                <div style={{ display: "flex", gap: 6 }}>
                  <button onClick={() => setEditing(m)}>Edit</button>
                  <button onClick={() => del(m.id)} style={{ color: "var(--warn)" }}>Del</button>
                </div>
              </div>
              <div className="muted" style={{ fontSize: 11 }}>{m.id.slice(0,8)} · {m.created_at?.slice(0,19)}</div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import TriagePanel from "../components/TriagePanel";
import MaturityBadge from "../components/MaturityBadge";

// Minimal markdown renderer — enough for body text from spec.md and phase docs.
// No external deps; safe-by-default escaping then a few transforms.
function renderMarkdown(md: string): string {
  const esc = (s: string) => s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  const lines = md.split("\n");
  const out: string[] = [];
  let para: string[] = [];
  const flush = () => {
    if (para.length) {
      const joined = para.join(" ");
      const html = esc(joined)
        .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>")
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
      out.push(`<p>${html}</p>`);
      para = [];
    }
  };
  for (const raw of lines) {
    const ln = raw.trimEnd();
    if (!ln.trim()) { flush(); continue; }
    if (/^#{1,3} /.test(ln)) {
      flush();
      const level = ln.match(/^(#+)/)![1].length;
      const txt = esc(ln.replace(/^#+\s+/, "")).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
      out.push(`<h${level + 2}>${txt}</h${level + 2}>`);
      continue;
    }
    if (/^[-*]\s+/.test(ln)) {
      flush();
      const txt = esc(ln.replace(/^[-*]\s+/, "")).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
      out.push(`<li>${txt}</li>`);
      continue;
    }
    para.push(ln);
  }
  flush();
  return out.join("\n");
}

type Comment = Awaited<ReturnType<typeof api.libraryComments>>[number];

const ROLE_LABEL: Record<string, string> = {
  prosecutor: "Атаковать прокурором",
  spackler: "Заштукатурить",
  sprout_advocate: "Защитить как росток",
  literal_alien: "Прочитать буквально",
};

const ROLE_HINT: Record<string, string> = {
  prosecutor: "будет бить по записи как по ложному клику",
  spackler: "подбросит гладкую заплатку поверх записи",
  sprout_advocate: "будет защищать запись от обвинения в слопе",
  literal_alien: "прочитает запись плоско, потеряв регистр",
};

const GAMES: { id: string; label: string }[] = [
  { id: "false_click",       label: "False Click" },
  { id: "missing_operation", label: "Missing Operation" },
  { id: "sprout_or_slop",    label: "Sprout or Slop" },
  { id: "register_sapper",   label: "Register Sapper" },
];

export default function LibraryEntry() {
  const { id } = useParams<{ id: string }>();
  const nav = useNavigate();
  const [entry, setEntry] = useState<any | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [convertBusy, setConvertBusy] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api.libraryEntry(id).then(setEntry).catch(() => setEntry(null));
    api.libraryComments(id).then(setComments).catch(() => {});
  }, [id]);

  async function genChimera() {
    if (!id) return;
    setConvertBusy("chimera");
    setErr(null);
    try {
      const r = await api.generateChimeraDraft(id);
      // navigate to configurator; designer can open the draft from there
      nav(`/configurator`);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally {
      setConvertBusy(null);
    }
  }

  async function playAs(gameId: string) {
    if (!id) return;
    setConvertBusy(gameId);
    setErr(null);
    try {
      const r = await api.convertEntry(id, gameId);
      nav(`/play/${gameId}?materialId=${r.material_id}`);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally {
      setConvertBusy(null);
    }
  }

  async function summon(role: string) {
    if (!id) return;
    setBusy(role);
    setErr(null);
    try {
      const c = await api.summonOrgan(id, role);
      setComments([c, ...comments]);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally {
      setBusy(null);
    }
  }

  if (!entry) return <div className="app"><div className="muted">Loading…</div></div>;

  return (
    <div className="app">
      <div className="header">
        <Link to={`/library/section/${entry.kind}`}>← раздел</Link>
        <span className="muted">{entry.code} · {entry.source_pass}{entry.source_line ? ` · L${entry.source_line}` : ""}</span>
        <MaturityBadge stage={entry.maturity_stage} />
        <select
          value={entry.maturity_stage ?? ""}
          onChange={async e => {
            const v = parseInt(e.target.value);
            if (Number.isNaN(v)) return;
            await api.patchMaturity(entry.id, v);
            setEntry({ ...entry, maturity_stage: v });
          }}
          style={{ width: "auto", fontSize: 11 }}
          title="изменить стадию зрелости"
        >
          {[0,1,2,3,4,5].map(s => <option key={s} value={s}>стадия {s}</option>)}
        </select>
      </div>
      <h2>{entry.title}</h2>

      <div
        className="card"
        style={{ lineHeight: 1.6 }}
        dangerouslySetInnerHTML={{ __html: renderMarkdown(entry.body_md) }}
      />

      {(entry.parents.length > 0 || entry.children.length > 0) && (
        <div className="card" style={{ marginTop: 12 }}>
          <div className="muted" style={{ fontSize: 12 }}>Связи</div>
          {entry.parents.map((p: any) => (
            <div key={p.id} style={{ marginTop: 4, fontSize: 12 }}>
              ← <Link to={`/library/entry/${p.id}`}>{p.code} {p.title}</Link> <span className="muted">({p.relation})</span>
            </div>
          ))}
          {entry.children.map((c: any) => (
            <div key={c.id} style={{ marginTop: 4, fontSize: 12 }}>
              → <Link to={`/library/entry/${c.id}`}>{c.code} {c.title}</Link> <span className="muted">({c.relation})</span>
            </div>
          ))}
        </div>
      )}

      <div className="card" style={{ marginTop: 16 }}>
        <div className="muted" style={{ fontSize: 12, marginBottom: 8 }}>
          Вызвать орган над этой записью. Один клик = один ход роли. Это не чат — давление одностороннее.
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {(["prosecutor", "spackler", "sprout_advocate", "literal_alien"] as const).map(r => (
            <button
              key={r}
              onClick={() => summon(r)}
              disabled={busy !== null}
              title={ROLE_HINT[r]}
            >
              {busy === r ? "Вызываю…" : ROLE_LABEL[r]}
            </button>
          ))}
        </div>
        {err && <div style={{ color: "var(--warn)", fontSize: 12, marginTop: 8 }}>{err}</div>}
      </div>

      {comments.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <div className="muted" style={{ fontSize: 12, marginBottom: 6 }}>Записанные ходы органов ({comments.length}):</div>
          {comments.map(c => (
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

      <TriagePanel entryId={entry.id} />

      {entry.kind === "chimera" && (
        <div className="card" style={{ marginTop: 16 }}>
          <div className="muted" style={{ fontSize: 12, marginBottom: 8 }}>
            Это ячейка химерной матрицы — скрещивание двух родов. Попроси chimera_weaver
            собрать черновик игры по этому скрещиванию. Он подберёт органы из 7 банков и
            отправит в /configurator.
          </div>
          <button
            className="primary"
            onClick={genChimera}
            disabled={convertBusy !== null}
          >
            {convertBusy === "chimera" ? "Прошу химеру…" : "Запросить химеру у LLM"}
          </button>
        </div>
      )}

      <div className="card" style={{ marginTop: 16 }}>
        <div className="muted" style={{ fontSize: 12, marginBottom: 8 }}>
          Сыграть на материале, выращенном из этой записи. Конвертер переведёт её тему в схему выбранной игры.
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {GAMES.map(g => (
            <button
              key={g.id}
              onClick={() => playAs(g.id)}
              disabled={convertBusy !== null}
              className="primary"
            >
              {convertBusy === g.id ? "Конвертирую…" : `Сыграть как ${g.label}`}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

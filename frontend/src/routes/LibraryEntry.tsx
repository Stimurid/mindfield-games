import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";

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

export default function LibraryEntry() {
  const { id } = useParams<{ id: string }>();
  const [entry, setEntry] = useState<any | null>(null);

  useEffect(() => {
    if (!id) return;
    api.libraryEntry(id).then(setEntry).catch(() => setEntry(null));
  }, [id]);

  if (!entry) return <div className="app"><div className="muted">Loading…</div></div>;

  return (
    <div className="app">
      <div className="header">
        <Link to={`/library/section/${entry.kind}`}>← раздел</Link>
        <span className="muted">{entry.code} · {entry.source_pass}{entry.source_line ? ` · L${entry.source_line}` : ""}</span>
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

      <div className="muted" style={{ fontSize: 11, marginTop: 12, fontStyle: "italic" }}>
        Phase 8 добавит сюда вызовы LLM-органов (атаковать прокурором / заштукатурить / защитить ростком / прочитать буквально).
        Phase 9 — кнопки «сыграть как ...» для конверсии в материал.
      </div>
    </div>
  );
}

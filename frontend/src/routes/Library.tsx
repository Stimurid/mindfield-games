import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

type Section = { kind: string; label: string; count: number };
type Hit = { id: string; code: string; kind: string; title: string; snippet: string };

export default function Library() {
  const [sections, setSections] = useState<Section[] | null>(null);
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<Hit[] | null>(null);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    api.librarySections().then(setSections).catch(() => {});
  }, []);

  async function runSearch(e: React.FormEvent) {
    e.preventDefault();
    const term = q.trim();
    if (term.length < 2) { setHits(null); return; }
    setSearching(true);
    try {
      setHits(await api.librarySearch(term));
    } finally {
      setSearching(false);
    }
  }

  return (
    <div className="app">
      <div className="header">
        <Link to="/">← все игры</Link>
        <span className="muted">Библиотека корпуса · топ-уровень</span>
      </div>

      <h2>Library</h2>
      <p className="muted" style={{ fontSize: 13 }}>
        Структурный слой исходного документа: 24 аттрактора, 12 R-корней, 12 пород, 40 химер,
        7 первых карточек, 8 остатков, 4 генома, 4 app-spec. Плюс наши документы фаз разработки.
        Мелкие карточки (4200+) подключим следующим проходом.
      </p>

      <form onSubmit={runSearch} style={{ marginTop: 16, display: "flex", gap: 8 }}>
        <input
          placeholder="Поиск по корпусу (минимум 2 символа)…"
          value={q}
          onChange={e => setQ(e.target.value)}
          style={{ flex: 1 }}
        />
        <button type="submit" disabled={searching}>Найти</button>
      </form>

      {hits !== null && (
        <div className="card" style={{ marginTop: 12 }}>
          <div className="muted" style={{ fontSize: 12 }}>{hits.length} результатов</div>
          {hits.map(h => (
            <Link key={h.id} to={`/library/entry/${h.id}`} style={{ display: "block", marginTop: 8, padding: 8, background: "var(--bg)", borderRadius: 4, textDecoration: "none", color: "inherit" }}>
              <div><span className="kbd">{h.code}</span> <b>{h.title}</b></div>
              <div className="muted" style={{ fontSize: 12, marginTop: 4 }} dangerouslySetInnerHTML={{ __html: h.snippet }} />
            </Link>
          ))}
        </div>
      )}

      <h3 style={{ marginTop: 24 }}>Разделы</h3>
      {!sections && <div className="muted">Loading…</div>}
      {sections?.map(s => (
        <Link key={s.kind} to={`/library/section/${s.kind}`} style={{ display: "block", textDecoration: "none", color: "inherit" }}>
          <div className="card" style={{ marginTop: 8, display: "flex", justifyContent: "space-between" }}>
            <span><b>{s.label}</b></span>
            <span className="kbd">{s.count}</span>
          </div>
        </Link>
      ))}
    </div>
  );
}

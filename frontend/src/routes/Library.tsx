import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useT } from "../i18n";

type Section = { kind: string; label: string; count: number };
type Hit = { id: string; code: string; kind: string; title: string; snippet: string };

export default function Library() {
  const t = useT();
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
        <Link to="/">← {t("все игры", "all games")}</Link>
        <span className="muted">{t("Библиотека корпуса · топ-уровень", "Corpus library · top level")}</span>
      </div>

      <h2>Library</h2>
      <p className="muted" style={{ fontSize: 13 }}>
        {t(
          "Структурный слой исходного документа: 24 аттрактора, 12 R-корней, 12 пород, 40 химер, 7 первых карточек, 8 остатков, 4 генома, 4 app-spec. Плюс наши документы фаз разработки. Мелкие карточки (4200+) подключены в Phase 12.",
          "Structural layer of the source document: 24 attractors, 12 R-roots, 12 breeds, 40 chimeras, 7 first cards, 8 residues, 4 genomes, 4 app-specs. Plus our phase-of-development docs. The 4200+ small cards are wired in Phase 12.",
        )}
      </p>

      <form onSubmit={runSearch} style={{ marginTop: 16, display: "flex", gap: 8 }}>
        <input
          placeholder={t("Поиск по корпусу (минимум 2 символа)…", "Search the corpus (min 2 chars)…")}
          value={q}
          onChange={e => setQ(e.target.value)}
          style={{ flex: 1 }}
        />
        <button type="submit" disabled={searching}>{t("Найти", "Search")}</button>
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

      <h3 style={{ marginTop: 24 }}>{t("Разделы", "Sections")}</h3>
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

import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";
import MaturityBadge from "../components/MaturityBadge";

const LABEL: Record<string, string> = {
  attractor: "Аттракторы",
  r_root: "Корневые операционные аттракторы",
  breed: "Породы",
  chimera: "Химерная матрица",
  precard: "Карточки 1-7",
  residual: "Остатки",
  genome: "Геномы первых четырёх",
  appspec: "App-spec",
  phase_doc: "Документы фаз разработки",
  micro_game: "Микро-игры (малое / игра / большой)",
  micro_numbered: "Нумерованные пункты",
  micro_bullet: "Bullet-пункты",
  micro_aspect: "Аспекты внутри пород / R-корней",
  source_section: "Разделы исходного корпуса 4200",
  source_card: "Сырые карточки 4200",
};

export default function LibrarySection() {
  const { kind } = useParams<{ kind: string }>();
  const [rows, setRows] = useState<any[] | null>(null);
  const [maturityFilter, setMaturityFilter] = useState<number | undefined>(undefined);

  useEffect(() => {
    if (!kind) return;
    api.libraryEntries(kind, maturityFilter).then(setRows).catch(() => setRows([]));
  }, [kind, maturityFilter]);

  if (!kind) return null;
  return (
    <div className="app">
      <div className="header">
        <Link to="/library">← библиотека</Link>
      </div>
      <h2>{LABEL[kind] ?? kind} <span className="muted" style={{ fontSize: 14 }}>· {rows?.length ?? "…"}</span></h2>

      <div className="card" style={{ marginTop: 8 }}>
        <div className="muted" style={{ fontSize: 12 }}>Фильтр стадии зрелости:</div>
        <div style={{ display: "flex", gap: 6, marginTop: 6 }}>
          <button onClick={() => setMaturityFilter(undefined)}
                  style={{ background: maturityFilter === undefined ? "rgba(80,160,80,0.25)" : "var(--bg)" }}>все</button>
          {[0,1,2,3,4,5].map(s => (
            <button key={s} onClick={() => setMaturityFilter(s)}
                    style={{ background: maturityFilter === s ? "rgba(80,160,80,0.25)" : "var(--bg)", fontSize: 12 }}>
              {s}
            </button>
          ))}
        </div>
      </div>

      {!rows && <div className="muted">Loading…</div>}
      {rows?.map(r => (
        <Link key={r.id} to={`/library/entry/${r.id}`} style={{ display: "block", textDecoration: "none", color: "inherit" }}>
          <div className="card" style={{ marginTop: 8 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <span className="kbd">{r.code}</span>{" "}
                <b>{r.title}</b>
              </div>
              <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                <MaturityBadge stage={r.maturity_stage} />
                <span className="muted" style={{ fontSize: 11 }}>{r.source_pass}</span>
              </div>
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}

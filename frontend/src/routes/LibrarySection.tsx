import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";

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

  useEffect(() => {
    if (!kind) return;
    api.libraryEntries(kind).then(setRows).catch(() => setRows([]));
  }, [kind]);

  if (!kind) return null;
  return (
    <div className="app">
      <div className="header">
        <Link to="/library">← библиотека</Link>
      </div>
      <h2>{LABEL[kind] ?? kind} <span className="muted" style={{ fontSize: 14 }}>· {rows?.length ?? "…"}</span></h2>
      {!rows && <div className="muted">Loading…</div>}
      {rows?.map(r => (
        <Link key={r.id} to={`/library/entry/${r.id}`} style={{ display: "block", textDecoration: "none", color: "inherit" }}>
          <div className="card" style={{ marginTop: 8 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <span className="kbd">{r.code}</span>{" "}
                <b>{r.title}</b>
              </div>
              <span className="muted" style={{ fontSize: 11 }}>{r.source_pass}</span>
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}

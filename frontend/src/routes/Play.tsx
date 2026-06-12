import { useEffect, useState } from "react";
import { useParams, useNavigate, Link, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import type { GameGenome, GameSession, Material } from "../types";
import GameShell from "../components/GameShell";

export default function Play() {
  const { gameId } = useParams<{ gameId: string }>();
  const [search, setSearch] = useSearchParams();
  const nav = useNavigate();
  const [genome, setGenome] = useState<GameGenome | null>(null);
  const [materials, setMaterials] = useState<Material[] | null>(null);
  const [material, setMaterial] = useState<Material | null>(null);
  const [session, setSession] = useState<GameSession | null>(null);
  const [err, setErr] = useState<string | null>(null);

  // Phase 1: load genome + materials list.
  useEffect(() => {
    if (!gameId) return;
    (async () => {
      try {
        const [g, mats] = await Promise.all([api.getGame(gameId), api.listMaterials(gameId)]);
        setGenome(g);
        if (!mats.length) throw new Error("no material seeded for this game");
        setMaterials(mats);
      } catch (e: any) {
        setErr(String(e));
      }
    })();
  }, [gameId]);

  // Phase 2: pick material (URL param wins; otherwise prefer first 'real' then 'demo').
  useEffect(() => {
    if (!materials || !gameId) return;
    const wanted = search.get("materialId");
    let chosen = materials.find(m => m.id === wanted);
    if (!chosen) {
      chosen = materials.find(m => m.namespace === "real") ?? materials[0];
    }
    (async () => {
      try {
        const mat = await api.getMaterial(chosen!.id);
        setMaterial(mat);
        const s = await api.createSession(gameId, mat.id);
        setSession(s);
      } catch (e: any) {
        setErr(String(e));
      }
    })();
  }, [materials, gameId, search.get("materialId")]);

  useEffect(() => {
    if (session?.status === "completed") {
      const t = setTimeout(() => nav(`/session/${session.id}/profile`), 600);
      return () => clearTimeout(t);
    }
  }, [session?.status]);

  function switchMaterial(id: string) {
    if (!gameId) return;
    setSession(null);
    setMaterial(null);
    setSearch({ materialId: id });
  }

  if (err) return <div className="app"><Link to="/">← back</Link><div className="card" style={{ color: "var(--warn)" }}>{err}</div></div>;
  if (!genome || !materials) return <div className="app"><div className="muted">Loading…</div></div>;

  return (
    <div className="app">
      <div className="header" style={{ flexWrap: "wrap", gap: 12 }}>
        <Link to="/">← все игры</Link>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <label className="muted" style={{ margin: 0 }}>Материал:</label>
          <select
            value={material?.id ?? ""}
            onChange={e => switchMaterial(e.target.value)}
            style={{ width: "auto" }}
          >
            {materials.map(m => (
              <option key={m.id} value={m.id}>
                {m.namespace === "real" ? "● real · " : "○ demo · "}{m.title}
              </option>
            ))}
          </select>
        </div>
        {session && <span className="muted">session <span className="kbd">{session.id.slice(0, 8)}</span></span>}
      </div>
      {(!material || !session) ? (
        <div className="muted">Загружаю материал…</div>
      ) : (
        <GameShell genome={genome} material={material} session={session} onChange={setSession} />
      )}
    </div>
  );
}

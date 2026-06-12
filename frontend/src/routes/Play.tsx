import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { api } from "../api/client";
import type { GameGenome, GameSession, Material } from "../types";
import GameShell from "../components/GameShell";

export default function Play() {
  const { gameId } = useParams<{ gameId: string }>();
  const nav = useNavigate();
  const [genome, setGenome] = useState<GameGenome | null>(null);
  const [material, setMaterial] = useState<Material | null>(null);
  const [session, setSession] = useState<GameSession | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!gameId) return;
    (async () => {
      try {
        const g = await api.getGame(gameId);
        setGenome(g);
        const mats = await api.listMaterials(gameId);
        if (!mats.length) throw new Error("no material seeded for this game");
        const mat = await api.getMaterial(mats[0].id);
        setMaterial(mat);
        const s = await api.createSession(gameId, mat.id);
        setSession(s);
      } catch (e: any) {
        setErr(String(e));
      }
    })();
  }, [gameId]);

  useEffect(() => {
    if (session?.status === "completed") {
      const t = setTimeout(() => nav(`/session/${session.id}/profile`), 600);
      return () => clearTimeout(t);
    }
  }, [session?.status]);

  if (err) return <div className="app"><Link to="/">← back</Link><div className="card" style={{ color: "var(--warn)" }}>{err}</div></div>;
  if (!genome || !material || !session) return <div className="app"><div className="muted">Loading…</div></div>;

  return (
    <div className="app">
      <div className="header">
        <Link to="/">← все игры</Link>
        <span className="muted">session <span className="kbd">{session.id.slice(0, 8)}</span></span>
      </div>
      <GameShell genome={genome} material={material} session={session} onChange={setSession} />
    </div>
  );
}

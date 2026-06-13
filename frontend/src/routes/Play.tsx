import { useEffect, useState } from "react";
import { useParams, useNavigate, Link, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import type { GameGenome, GameSession, Material } from "../types";
import GameShell from "../components/GameShell";

// Game-aware playtest defaults — picked from the 302.ai gauntlet:
// gpt-4.1-mini holds prosecutor/spackler/sprout_advocate cleanly and is faster;
// literal_alien (Register Sapper) needs grok-4-0709 to avoid generic blindness.
function gameDefaultModel(gameId: string | undefined): string {
  if (gameId === "register_sapper") return "grok-4-0709";
  return "gpt-4.1-mini";
}

function modelStorageKey(gameId: string | undefined): string {
  return gameId ? `mindfield.model.${gameId}` : "mindfield.model";
}

export default function Play() {
  const { gameId } = useParams<{ gameId: string }>();
  const [search, setSearch] = useSearchParams();
  const nav = useNavigate();
  const [genome, setGenome] = useState<GameGenome | null>(null);
  const [materials, setMaterials] = useState<Material[] | null>(null);
  const [material, setMaterial] = useState<Material | null>(null);
  const [session, setSession] = useState<GameSession | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [models, setModels] = useState<{ id: string; label: string; gateway: string }[]>([]);
  const [model, setModel] = useState<string>("");
  const [overridden, setOverridden] = useState(false);

  useEffect(() => {
    api.listModels().then(r => setModels(r.presets)).catch(() => {});
  }, []);

  // Pick the active model whenever the game changes.
  // Priority: per-game saved override > game-aware default.
  // Selected model is mirrored into the global key the api client reads.
  useEffect(() => {
    if (!gameId) return;
    const perGame = localStorage.getItem(modelStorageKey(gameId));
    const def = gameDefaultModel(gameId);
    const chosen = perGame || def;
    setOverridden(Boolean(perGame) && perGame !== def);
    setModel(chosen);
    localStorage.setItem("mindfield.model", chosen);
  }, [gameId]);

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

  function onModelChange(next: string) {
    if (!gameId) return;
    setModel(next);
    localStorage.setItem("mindfield.model", next);
    const def = gameDefaultModel(gameId);
    if (next === def) {
      localStorage.removeItem(modelStorageKey(gameId));
      setOverridden(false);
    } else {
      localStorage.setItem(modelStorageKey(gameId), next);
      setOverridden(true);
    }
  }

  if (err) return <div className="app"><Link to="/">← back</Link><div className="card" style={{ color: "var(--warn)" }}>{err}</div></div>;
  if (!genome || !materials) return <div className="app"><div className="muted">Loading…</div></div>;

  const activeModelMeta = models.find(m => m.id === model);

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
        {models.length > 0 && (
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <label className="muted" style={{ margin: 0 }}>LLM:</label>
            <select
              value={model}
              onChange={e => onModelChange(e.target.value)}
              style={{ width: "auto" }}
            >
              {models.map(m => (
                <option key={m.id} value={m.id}>{m.label} · {m.gateway}</option>
              ))}
            </select>
          </div>
        )}
        {activeModelMeta && (
          <span
            className="kbd"
            title={overridden ? "manual override of game default" : "playtest default for this game"}
            style={{
              background: overridden ? "rgba(220,160,0,0.15)" : "rgba(80,160,80,0.15)",
              color: overridden ? "var(--warn)" : "var(--accent)",
            }}
          >
            active · {activeModelMeta.label}{overridden ? " (manual)" : ""}
          </span>
        )}
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

import type { GameGenome, GameSession, Material, LLMIntervention, PlayerMove } from "../types";

const BASE = "";

async function j<T>(r: Response): Promise<T> {
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json() as Promise<T>;
}

// Lightweight player identity — UUID stored in localStorage, sent on every
// session-creating call so Phase 6 aggregation can stitch sessions per player.
function getPlayerToken(): string {
  let t = localStorage.getItem("mindfield.player_token");
  if (!t) {
    t = (crypto.randomUUID?.() ?? `p${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`);
    localStorage.setItem("mindfield.player_token", t);
  }
  return t;
}

function tokHeaders(): Record<string, string> {
  return { "Content-Type": "application/json", "X-Player-Token": getPlayerToken() };
}

export const api = {
  listGames: () => fetch(`${BASE}/api/games`).then(j<GameGenome[]>),
  getGame: (id: string) => fetch(`${BASE}/api/games/${id}`).then(j<GameGenome>),
  listMaterials: (gameId: string) =>
    fetch(`${BASE}/api/materials?gameId=${gameId}`).then(j<Material[]>),
  getMaterial: (id: string) => fetch(`${BASE}/api/materials/${id}`).then(j<Material>),
  createSession: (gameId: string, materialId?: string) =>
    fetch(`${BASE}/api/sessions`, {
      method: "POST",
      headers: tokHeaders(),
      body: JSON.stringify({ game_id: gameId, material_id: materialId }),
    }).then(j<GameSession>),
  replay: (sessionId: string, model?: string) =>
    fetch(`${BASE}/api/sessions/${sessionId}/replay`, {
      method: "POST",
      headers: tokHeaders(),
      body: JSON.stringify({ model }),
    }).then(j<{ new_session_id: string; new_material_id: string; mutation_directive: string; parent_material_id: string; parent_session_id: string }>),
  getSession: (id: string) => fetch(`${BASE}/api/sessions/${id}`).then(j<GameSession>),
  postMove: (sid: string, body: { round_id: string; action: string; target_unit_id?: string | null; payload: any }) =>
    fetch(`${BASE}/api/sessions/${sid}/moves`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(j<PlayerMove>),
  llmIntervene: (sid: string, role: string, context: any, move_ids: string[] = [], model?: string) => {
    const m = model ?? localStorage.getItem("mindfield.model") ?? undefined;
    return fetch(`${BASE}/api/sessions/${sid}/llm-intervention`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role, context, move_ids, model: m }),
    }).then(j<LLMIntervention>);
  },
  listModels: () =>
    fetch(`${BASE}/api/llm/models`).then(j<{ presets: { id: string; label: string; gateway: string }[]; default: string; provider: string }>),
  getOperatorProfile: () =>
    fetch(`${BASE}/api/operator/me`, { headers: { "X-Player-Token": getPlayerToken() } }).then(j<{
      player_token: string;
      coverage: string;
      games_played: string[];
      per_game: Record<string, { session_id: string; completed_at: string | null; dimensions: Record<string, any>; replay_directives: string[] }>;
      explicit_dimensions: string[];
      cross_patterns: string[];
      verdict: string;
    }>),
  librarySections: () =>
    fetch(`${BASE}/api/library/sections`).then(j<{ kind: string; label: string; count: number }[]>),
  libraryEntries: (kind?: string) =>
    fetch(`${BASE}/api/library/entries${kind ? `?kind=${kind}` : ""}`).then(j<{ id: string; code: string; kind: string; title: string; source_pass: string; source_line: number | null }[]>),
  libraryEntry: (id: string) =>
    fetch(`${BASE}/api/library/entries/${id}`).then(j<{ id: string; code: string; kind: string; title: string; body_md: string; source_pass: string; source_line: number | null; parents: any[]; children: any[] }>),
  librarySearch: (q: string, kind?: string) =>
    fetch(`${BASE}/api/library/search?q=${encodeURIComponent(q)}${kind ? `&kind=${kind}` : ""}`).then(j<{ id: string; code: string; kind: string; title: string; snippet: string }[]>),
  complete: (sid: string) =>
    fetch(`${BASE}/api/sessions/${sid}/complete`, { method: "POST" }).then(j<GameSession>),
  exportMd: (sid: string) =>
    fetch(`${BASE}/api/sessions/${sid}/export?format=md`).then(r => r.text()),
};

import type { GameGenome, GameSession, Material, LLMIntervention, PlayerMove } from "../types";

const BASE = "";

async function j<T>(r: Response): Promise<T> {
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json() as Promise<T>;
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
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_id: gameId, material_id: materialId }),
    }).then(j<GameSession>),
  getSession: (id: string) => fetch(`${BASE}/api/sessions/${id}`).then(j<GameSession>),
  postMove: (sid: string, body: { round_id: string; action: string; target_unit_id?: string | null; payload: any }) =>
    fetch(`${BASE}/api/sessions/${sid}/moves`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(j<PlayerMove>),
  llmIntervene: (sid: string, role: string, context: any, move_ids: string[] = []) =>
    fetch(`${BASE}/api/sessions/${sid}/llm-intervention`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role, context, move_ids }),
    }).then(j<LLMIntervention>),
  complete: (sid: string) =>
    fetch(`${BASE}/api/sessions/${sid}/complete`, { method: "POST" }).then(j<GameSession>),
  exportMd: (sid: string) =>
    fetch(`${BASE}/api/sessions/${sid}/export?format=md`).then(r => r.text()),
};

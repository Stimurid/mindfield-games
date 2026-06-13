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
  libraryEntries: (kind?: string, maturity?: number) => {
    const params = new URLSearchParams();
    if (kind) params.set("kind", kind);
    if (maturity !== undefined) params.set("maturity", String(maturity));
    const qs = params.toString();
    return fetch(`${BASE}/api/library/entries${qs ? "?" + qs : ""}`).then(j<{ id: string; code: string; kind: string; title: string; source_pass: string; source_line: number | null; maturity_stage: number | null }[]>);
  },
  patchMaturity: (entryId: string, maturity_stage: number) =>
    fetch(`${BASE}/api/library/entries/${entryId}/maturity`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ maturity_stage }),
    }).then(j<{ id: string; maturity_stage: number }>),
  libraryEntry: (id: string) =>
    fetch(`${BASE}/api/library/entries/${id}`).then(j<{ id: string; code: string; kind: string; title: string; body_md: string; source_pass: string; source_line: number | null; parents: any[]; children: any[] }>),
  configBanks: () =>
    fetch(`${BASE}/api/configurator/banks`).then(j<{ bank: string; label: string; hint: string; count: number; is_degradation: boolean }[]>),
  configOrgans: (bank?: string) =>
    fetch(`${BASE}/api/configurator/organs${bank ? `?bank=${bank}` : ""}`).then(j<{ id: string; bank: string; code: string; name: string; description: string | null; source: string }[]>),
  configCreateDraft: (payload: { name: string; function?: string; verb?: string; maturity_stage?: number; selected_organs?: Record<string, string[]> }) =>
    fetch(`${BASE}/api/configurator/drafts`, {
      method: "POST",
      headers: tokHeaders(),
      body: JSON.stringify(payload),
    }).then(j<any>),
  configListDrafts: (mine = true) =>
    fetch(`${BASE}/api/configurator/drafts${mine ? "?mine=true" : ""}`, { headers: { "X-Player-Token": getPlayerToken() } }).then(j<any[]>),
  configGetDraft: (id: string) =>
    fetch(`${BASE}/api/configurator/drafts/${id}`).then(j<any>),
  configPatchDraft: (id: string, payload: any) =>
    fetch(`${BASE}/api/configurator/drafts/${id}`, {
      method: "PATCH",
      headers: tokHeaders(),
      body: JSON.stringify(payload),
    }).then(j<any>),
  configRunWeaver: (id: string, model?: string) =>
    fetch(`${BASE}/api/configurator/drafts/${id}/weaver`, {
      method: "POST",
      headers: tokHeaders(),
      body: JSON.stringify({ model }),
    }).then(j<{ draft: any; verdict: { verb_status: string; crisis_status: string; trace_status: string; degradation_warnings: string[]; playable_verdict: string; critique: string } }>),
  triageFates: () =>
    fetch(`${BASE}/api/triage/fates`).then(j<{ fate: string; label: string }[]>),
  triageEntry: (entryId: string) =>
    fetch(`${BASE}/api/triage/entries/${entryId}`).then(j<any[]>),
  assignFate: (entryId: string, payload: { fate: string; note?: string; organ_bank?: string; organ_name?: string }) =>
    fetch(`${BASE}/api/triage/entries/${entryId}`, {
      method: "POST",
      headers: tokHeaders(),
      body: JSON.stringify(payload),
    }).then(j<any>),
  triageQueue: (kind = "source_card", limit = 25) =>
    fetch(`${BASE}/api/triage/queue?kind=${kind}&limit=${limit}`, { headers: { "X-Player-Token": getPlayerToken() } }).then(j<{ id: string; code: string; title: string; kind: string; body_md: string }[]>),
  triageStats: (mine = true) =>
    fetch(`${BASE}/api/triage/stats?mine=${mine}`, { headers: { "X-Player-Token": getPlayerToken() } }).then(j<{ total_verdicts: number; by_fate: { fate: string; label: string; count: number }[]; extracted_organs: number }>),
  // Admin
  adminListMaterials: () =>
    fetch(`${BASE}/api/admin/materials`).then(j<any[]>),
  adminCreateMaterial: (payload: any) =>
    fetch(`${BASE}/api/admin/materials`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(j<any>),
  adminUpdateMaterial: (id: string, payload: any) =>
    fetch(`${BASE}/api/admin/materials/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(j<any>),
  adminDeleteMaterial: (id: string) =>
    fetch(`${BASE}/api/admin/materials/${id}`, { method: "DELETE" }).then(j<{ deleted: string }>),
  // Research
  researchListHypotheses: (mine = true) =>
    fetch(`${BASE}/api/research/hypotheses?mine=${mine}`, { headers: { "X-Player-Token": getPlayerToken() } }).then(j<any[]>),
  researchGetHypothesis: (id: string) =>
    fetch(`${BASE}/api/research/hypotheses/${id}`).then(j<any>),
  researchCreateHypothesis: (payload: { title: string; body_md?: string; tags?: string[]; linked_draft_id?: string | null }) =>
    fetch(`${BASE}/api/research/hypotheses`, {
      method: "POST",
      headers: tokHeaders(),
      body: JSON.stringify(payload),
    }).then(j<any>),
  researchPatchHypothesis: (id: string, payload: any) =>
    fetch(`${BASE}/api/research/hypotheses/${id}`, {
      method: "PATCH",
      headers: tokHeaders(),
      body: JSON.stringify(payload),
    }).then(j<any>),
  researchDeleteHypothesis: (id: string) =>
    fetch(`${BASE}/api/research/hypotheses/${id}`, { method: "DELETE" }).then(j<{ deleted: string }>),
  researchDiscussions: (id: string) =>
    fetch(`${BASE}/api/research/hypotheses/${id}/discussions`).then(j<any[]>),
  researchSummon: (id: string, role: string, angle?: string, model?: string) =>
    fetch(`${BASE}/api/research/hypotheses/${id}/summon`, {
      method: "POST",
      headers: tokHeaders(),
      body: JSON.stringify({ role, angle, model }),
    }).then(j<any>),
  // Configurator promotion
  configListFieldTypes: () =>
    fetch(`${BASE}/api/configurator/field-types`).then(j<{ id: string; label: string }[]>),
  configPromoteDraft: (id: string, field_type: string, source_seed_material_id?: string) =>
    fetch(`${BASE}/api/configurator/drafts/${id}/promote`, {
      method: "POST",
      headers: tokHeaders(),
      body: JSON.stringify({ field_type, source_seed_material_id }),
    }).then(j<{ draft_id: string; promoted_game_id: string; field_type: string; source_seed_material_id: string | null }>),
  librarySearch: (q: string, kind?: string) =>
    fetch(`${BASE}/api/library/search?q=${encodeURIComponent(q)}${kind ? `&kind=${kind}` : ""}`).then(j<{ id: string; code: string; kind: string; title: string; snippet: string }[]>),
  libraryComments: (entryId: string) =>
    fetch(`${BASE}/api/library/entries/${entryId}/comments`).then(j<{ id: string; role: string; angle: string | null; output: any; model: string | null; created_at: string | null }[]>),
  generateChimeraDraft: (entryId: string, model?: string) =>
    fetch(`${BASE}/api/library/entries/${entryId}/generate-chimera-draft`, {
      method: "POST",
      headers: tokHeaders(),
      body: JSON.stringify({ model }),
    }).then(j<{ draft_id: string; name: string; function: string; verb: string; maturity_stage: number; selected_organs: Record<string, string[]>; critique: string; source_chimera_id: string }>),
  convertEntry: (entryId: string, gameId: string, model?: string) =>
    fetch(`${BASE}/api/library/entries/${entryId}/convert`, {
      method: "POST",
      headers: tokHeaders(),
      body: JSON.stringify({ game_id: gameId, model }),
    }).then(j<{ material_id: string; game_id: string; title: string; namespace: string; source_corpus_id: string }>),
  summonOrgan: (entryId: string, role: string, angle?: string, model?: string) =>
    fetch(`${BASE}/api/library/entries/${entryId}/summon`, {
      method: "POST",
      headers: tokHeaders(),
      body: JSON.stringify({ role, angle, model }),
    }).then(j<{ id: string; role: string; angle: string | null; output: any; model: string | null; created_at: string | null }>),
  complete: (sid: string) =>
    fetch(`${BASE}/api/sessions/${sid}/complete`, { method: "POST" }).then(j<GameSession>),
  exportMd: (sid: string) =>
    fetch(`${BASE}/api/sessions/${sid}/export?format=md`).then(r => r.text()),
};

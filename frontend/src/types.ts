export type FieldType =
  | "clickable_text_units"
  | "gap_click_text"
  | "card_sorting"
  | "medium_shift_phrase";

export interface GameRound {
  id: string;
  title: string;
  instruction: string;
  time_sec: number;
}

export interface GameGenome {
  id: string;
  title: string;
  short_title: string;
  function: string;
  field_type: FieldType;
  rounds: GameRound[];
  player_actions: string[];
  verdicts?: string[];
  fates?: string[];
  absence_types?: string[];
  mediums?: string[];
  phrase_actions?: string[];
  llm_roles: { id: string; triggered_on_action: string }[];
  toxins?: string[];
}

export interface Material {
  id: string;
  game_id: string;
  title: string;
  payload: any;
}

export interface PlayerMove {
  id: string;
  round_id: string;
  action: string;
  target_unit_id?: string | null;
  payload: Record<string, any>;
  created_at: string;
}

export interface LLMIntervention {
  id: string;
  role: string;
  output: Record<string, any>;
  created_at: string;
}

export interface GameSession {
  id: string;
  game_id: string;
  material_id: string;
  status: "created" | "in_progress" | "completed";
  current_round_id: string | null;
  started_at: string;
  completed_at: string | null;
  trace_profile: any;
  moves: PlayerMove[];
  interventions: LLMIntervention[];
}

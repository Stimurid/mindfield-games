import type { GameSession } from "../types";

const ACTION_MEANING: Record<string, string> = {
  select_unit: "вы заявили фразу как несущий узел — это вызовет прокурора",
  prove_operation: "вы привязали операцию к фразе — прокурор уже знает, что атаковать",
  assign_verdict: "вы зафиксировали финальный статус — это входит в профиль ложного клика",
  click_gap: "вы указали место разрыва — теперь нужно назвать тип отсутствия",
  assign_absence_type: "вы назвали отсутствие — шпаклёвщик подбросит ложную заплатку",
  respond_to_patch: "вы решили судьбу заплатки — это входит в patch_susceptibility",
  assign_fate: "вы назначили судьбу дыре — это финал по этому отсутствию",
  sort_card: "вы поставили карточке судьбу — адвокат может вмешаться",
  defend_fate: "вы подтвердили судьбу под давлением — это входит в profile",
  revise_fate: "вы изменили судьбу — это входит в selection_bias",
  set_incubation_test: "вы дали ростку срок и способ проверки — это спасает от 'incubate без обязательств'",
  assign_phrase_action: "вы назвали действие фразы, а не её тон",
  compare_medium_shift: "вы зафиксировали сдвиг при смене медиума — literal_alien вмешается",
  repair_machine_reading: "вы починили буквальное чтение — это входит в medium_awareness",
  transfer_phrase: "вы перенесли фразу, сохраняя действие — это входит в transfer_accuracy",
};

export default function TracePanel({ session }: { session: GameSession }) {
  const entries = [
    ...session.moves.map(m => ({ kind: "move" as const, when: m.created_at, m })),
    ...session.interventions.map(iv => ({ kind: "llm" as const, when: iv.created_at, iv })),
  ].sort((a, b) => (a.when ?? "").localeCompare(b.when ?? ""));

  return (
    <div className="trace-panel">
      <div className="muted" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 6 }}>
        Trace · что каждый ход меняет
      </div>
      {entries.length === 0 && <div className="muted" style={{ fontSize: 12 }}>пока пусто — сделай ход в поле</div>}
      {entries.map((e, i) => (
        <div key={i} className="trace-entry">
          {e.kind === "move" ? (
            <>
              <span className="action">{e.m.action}</span>
              {e.m.target_unit_id && <> · <span className="kbd">{e.m.target_unit_id}</span></>}
              <div className="muted" style={{ fontSize: 11, fontStyle: "italic" }}>
                {ACTION_MEANING[e.m.action] ?? "ход зафиксирован в trace"}
              </div>
              {e.m.payload && Object.keys(e.m.payload).length > 0 && (
                <div className="muted" style={{ fontSize: 11 }}>{JSON.stringify(e.m.payload)}</div>
              )}
            </>
          ) : (
            <>
              <span className="action" style={{ color: "var(--warn)" }}>llm · {e.iv.role}</span>
              <div className="muted" style={{ fontSize: 11 }}>
                сопротивление от {e.iv.role} — не ответ, а ход
              </div>
            </>
          )}
        </div>
      ))}
    </div>
  );
}

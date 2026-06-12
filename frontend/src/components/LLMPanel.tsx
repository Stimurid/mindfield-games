import type { GameGenome, GameSession } from "../types";

const ROLE_DESC: Record<string, string> = {
  prosecutor: "атакует ваш выбор. Не помогает. Не отвечает на вопросы.",
  spackler: "подкидывает гладкую заплатку, которая прячет дыру. Не раскрывает правильный ответ.",
  sprout_advocate: "спорит с вашей судьбой карточки. Защищает вырезанное, атакует сохранённое.",
  literal_alien: "читает фразу буквально и теряет регистр, адресата, мем, шутку. Сам себя не чинит.",
};

export default function LLMPanel({ genome, session }: { genome: GameGenome; session: GameSession }) {
  const last = session.interventions[session.interventions.length - 1];
  const roleIds = genome.llm_roles.map(r => r.id);
  return (
    <div className="llm-panel">
      <div className="muted" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5 }}>
        LLM organ <span style={{ color: "var(--warn)" }}>· NOT an assistant</span>
      </div>
      <div style={{ fontSize: 13, marginTop: 4 }}>
        {roleIds.map(r => (
          <div key={r} style={{ marginTop: 4 }}>
            <span className="kbd">{r}</span>{" "}
            <span className="muted">{ROLE_DESC[r] ?? "игровой орган сцены"}</span>
          </div>
        ))}
      </div>
      {last ? (
        <div style={{ marginTop: 12, fontSize: 13 }}>
          <div className="llm-role-tag">{last.role} · последнее вмешательство</div>
          {Object.entries(last.output).filter(([k]) => !k.startsWith("_")).map(([k, v]) => (
            <div key={k} style={{ marginTop: 4 }}>
              <b>{k}:</b>{" "}
              {Array.isArray(v) ? <ul style={{ margin: "4px 0 0 16px" }}>{(v as string[]).map((x, i) => <li key={i}>{x}</li>)}</ul> : String(v)}
            </div>
          ))}
        </div>
      ) : (
        <div className="muted" style={{ marginTop: 12, fontSize: 12 }}>
          (роль молчит, пока вы не сделаете ход в поле — она не чат)
        </div>
      )}
    </div>
  );
}

import type { GameGenome, GameSession } from "../types";

export default function LLMPanel({ genome, session }: { genome: GameGenome; session: GameSession }) {
  const last = session.interventions[session.interventions.length - 1];
  const roleIds = genome.llm_roles.map(r => r.id);
  return (
    <div className="llm-panel">
      <div className="muted" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5 }}>LLM organ</div>
      <div style={{ fontSize: 13, marginTop: 4 }}>
        Роли в этой игре: {roleIds.map(r => <span key={r} className="kbd" style={{ marginRight: 4 }}>{r}</span>)}
      </div>
      <div style={{ marginTop: 8, fontSize: 12, color: "var(--fg-dim)" }}>
        Модель здесь не ассистент. Она сопротивляется, шпаклюет, спорит или буквализирует.
      </div>
      {last && (
        <div style={{ marginTop: 12, fontSize: 13 }}>
          <div className="llm-role-tag">{last.role} · последнее вмешательство</div>
          {Object.entries(last.output).filter(([k]) => !k.startsWith("_")).map(([k, v]) => (
            <div key={k} style={{ marginTop: 4 }}>
              <b>{k}:</b>{" "}
              {Array.isArray(v) ? <ul style={{ margin: "4px 0 0 16px" }}>{(v as string[]).map((x, i) => <li key={i}>{x}</li>)}</ul> : String(v)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

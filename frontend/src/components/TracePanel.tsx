import type { GameSession } from "../types";

export default function TracePanel({ session }: { session: GameSession }) {
  const entries = [
    ...session.moves.map(m => ({ kind: "move" as const, when: m.created_at, m })),
    ...session.interventions.map(iv => ({ kind: "llm" as const, when: iv.created_at, iv })),
  ].sort((a, b) => (a.when ?? "").localeCompare(b.when ?? ""));

  return (
    <div className="trace-panel">
      <div className="muted" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 6 }}>Trace</div>
      {entries.length === 0 && <div className="muted" style={{ fontSize: 12 }}>пока пусто — сделай ход в поле</div>}
      {entries.map((e, i) => (
        <div key={i} className="trace-entry">
          {e.kind === "move" ? (
            <>
              <span className="action">{e.m.action}</span>
              {e.m.target_unit_id && <> · <span className="kbd">{e.m.target_unit_id}</span></>}
              {e.m.payload && Object.keys(e.m.payload).length > 0 && (
                <div className="muted" style={{ fontSize: 11 }}>{JSON.stringify(e.m.payload)}</div>
              )}
            </>
          ) : (
            <>
              <span className="action" style={{ color: "var(--warn)" }}>llm · {e.iv.role}</span>
              <div className="muted" style={{ fontSize: 11 }}>
                {Object.keys(e.iv.output).filter(k => !k.startsWith("_")).join(", ")}
              </div>
            </>
          )}
        </div>
      ))}
    </div>
  );
}

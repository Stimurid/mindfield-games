import type { GameGenome, GameSession } from "../types";

export default function RoundHeader({ genome, session }: { genome: GameGenome; session: GameSession }) {
  const round = genome.rounds.find(r => r.id === session.current_round_id) ?? genome.rounds[0];
  return (
    <div className="card round-header">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <h2 style={{ margin: 0 }}>{genome.title}</h2>
        <span className="muted">round {genome.rounds.findIndex(r => r.id === round.id) + 1}/{genome.rounds.length} · <b>{round.title}</b></span>
      </div>
      <div className="muted" style={{ marginTop: 4 }}>{round.instruction}</div>
    </div>
  );
}

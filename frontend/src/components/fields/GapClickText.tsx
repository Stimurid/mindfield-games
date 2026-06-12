import { useState } from "react";
import type { GameGenome, GameSession, Material } from "../../types";
import { api } from "../../api/client";

interface Props {
  genome: GameGenome;
  material: Material;
  session: GameSession;
  onChange: (s: GameSession) => void;
}

export default function GapClickText({ genome, material, session, onChange }: Props) {
  const blocks = material.payload.blocks as { id: string; text: string }[];
  const gaps = material.payload.gaps as { id: string; between: [string, string]; dev_absence?: string }[];
  const [clickedGaps, setClickedGaps] = useState<string[]>([]);
  const [absenceType, setAbsenceType] = useState<Record<string, string>>({});
  const [patches, setPatches] = useState<Record<string, { patch: string; risk: string }>>({});
  const [patchResp, setPatchResp] = useState<Record<string, string>>({});
  const [fates, setFates] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);

  const ABSENCE = genome.absence_types ?? [];
  const FATES = genome.fates ?? [];

  function refresh() { api.getSession(session.id).then(onChange); }

  async function clickGap(gid: string) {
    if (clickedGaps.includes(gid)) return;
    if (clickedGaps.length >= 3) return;
    setClickedGaps([...clickedGaps, gid]);
    await api.postMove(session.id, {
      round_id: "gap", action: "click_gap", target_unit_id: gid, payload: { gap_id: gid },
    });
    refresh();
  }

  async function chooseAbsence(gid: string, type: string) {
    setAbsenceType(prev => ({ ...prev, [gid]: type }));
    await api.postMove(session.id, {
      round_id: "gap", action: "assign_absence_type", target_unit_id: gid, payload: { absence_type: type },
    });
    setBusy(true);
    const gap = gaps.find(g => g.id === gid)!;
    const ctxText = gap.between.map(bid => blocks.find(b => b.id === bid)?.text).filter(Boolean).join(" ⇆ ");
    const iv = await api.llmIntervene(session.id, "spackler", {
      gap_context: ctxText, absence_type: type,
    });
    setPatches(prev => ({ ...prev, [gid]: { patch: iv.output.patch, risk: iv.output.risk } }));
    setBusy(false);
    refresh();
  }

  async function respondPatch(gid: string, resp: string) {
    setPatchResp(prev => ({ ...prev, [gid]: resp }));
    await api.postMove(session.id, {
      round_id: "patch", action: "respond_to_patch", target_unit_id: gid, payload: { response: resp },
    });
    refresh();
  }

  async function setFate(gid: string, fate: string) {
    setFates(prev => ({ ...prev, [gid]: fate }));
    await api.postMove(session.id, {
      round_id: "fate", action: "assign_fate", target_unit_id: gid, payload: { fate },
    });
    refresh();
  }

  async function finish() {
    setBusy(true);
    const s = await api.complete(session.id);
    onChange(s);
    setBusy(false);
  }

  const allDone = clickedGaps.length > 0 && clickedGaps.every(g => fates[g]);

  return (
    <div>
      <p className="muted">{material.payload.intro}</p>
      <div>
        {blocks.map((b, i) => (
          <div key={b.id}>
            <div className="block">{b.text}</div>
            {(() => {
              const gap = gaps.find(g => g.between[0] === b.id && g.between[1] === blocks[i + 1]?.id);
              if (!gap) return null;
              const isClicked = clickedGaps.includes(gap.id);
              return (
                <div>
                  <div
                    className={"gap" + (isClicked ? " clicked" : "")}
                    onClick={() => clickGap(gap.id)}
                  />
                  {isClicked && (
                    <div className="card" style={{ margin: "4px 0" }}>
                      <label>Тип отсутствия</label>
                      <select
                        value={absenceType[gap.id] ?? ""}
                        onChange={e => chooseAbsence(gap.id, e.target.value)}
                        disabled={!!absenceType[gap.id]}
                      >
                        <option value="">—</option>
                        {ABSENCE.map(a => <option key={a} value={a}>{a}</option>)}
                      </select>
                      {patches[gap.id] && (
                        <div style={{ marginTop: 8, padding: 8, background: "var(--bg)", borderRadius: 4 }}>
                          <div className="llm-role-tag">spackler</div>
                          <div><b>patch:</b> {patches[gap.id].patch}</div>
                          <div><b>risk:</b> <span className="muted">{patches[gap.id].risk}</span></div>
                          <div className="actions-bar">
                            {["accept", "repair", "reject"].map(r => (
                              <button
                                key={r}
                                className={patchResp[gap.id] === r ? "primary" : ""}
                                onClick={() => respondPatch(gap.id, r)}
                              >{r}</button>
                            ))}
                          </div>
                        </div>
                      )}
                      {patchResp[gap.id] && (
                        <div style={{ marginTop: 8 }}>
                          <label>Судьба отсутствия</label>
                          <select value={fates[gap.id] ?? ""} onChange={e => setFate(gap.id, e.target.value)}>
                            <option value="">—</option>
                            {FATES.map(f => <option key={f} value={f}>{f}</option>)}
                          </select>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        ))}
      </div>
      <div className="actions-bar">
        <button className="primary" disabled={!allDone || busy} onClick={finish}>
          Завершить
        </button>
        <span className="muted">отмечено {clickedGaps.length}/3</span>
      </div>
    </div>
  );
}

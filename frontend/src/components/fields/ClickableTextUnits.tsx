import { useState } from "react";
import type { GameGenome, GameSession, Material } from "../../types";
import { api } from "../../api/client";

interface Props {
  genome: GameGenome;
  material: Material;
  session: GameSession;
  onChange: (s: GameSession) => void;
}

const VERDICTS = ["bearing_node", "false_click", "weak_sprout", "service_phrase"] as const;
const VERDICT_MEANING: Record<string, string> = {
  bearing_node:   "Стою на своём — операция настоящая, атаки прокурора не валят её",
  weak_sprout:    "Я был частично прав, но операция слабее, чем я заявил",
  false_click:    "Признаю — прокурор прав, я кликнул на форму, а не на операцию",
  service_phrase: "Это вообще соединительный шов, не несущий узел",
};
const BIAS_HINTS = ["dramatic_phrase", "abstract_word", "familiar_topic", "pseudo_depth", "conclusion_like_phrase"];

export default function ClickableTextUnits({ genome, material, session, onChange }: Props) {
  const units = material.payload.units as { id: string; index: number; text: string }[];
  const [selected, setSelected] = useState<string[]>([]);
  const [ops, setOps] = useState<Record<string, string>>({});
  const [biases, setBiases] = useState<Record<string, string>>({});
  const [attacks, setAttacks] = useState<Record<string, any>>({});
  const [verdicts, setVerdicts] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);

  const round = session.current_round_id ?? "select";

  function refresh() {
    api.getSession(session.id).then(onChange);
  }

  async function toggleSelect(uid: string, bias: string) {
    if (selected.includes(uid)) {
      setSelected(selected.filter(x => x !== uid));
      return;
    }
    if (selected.length >= 3) return;
    setSelected([...selected, uid]);
    setBiases(prev => ({ ...prev, [uid]: bias }));
    await api.postMove(session.id, {
      round_id: "select",
      action: "select_unit",
      target_unit_id: uid,
      payload: { hint_bias: bias },
    });
    refresh();
  }

  async function proveAndAttack(uid: string) {
    if (!ops[uid]) return;
    setBusy(true);
    await api.postMove(session.id, {
      round_id: "prove",
      action: "prove_operation",
      target_unit_id: uid,
      payload: { operation: ops[uid] },
    });
    const unit = units.find(u => u.id === uid)!;
    const iv = await api.llmIntervene(session.id, "prosecutor", {
      phrase: unit.text,
      claimed_operation: ops[uid],
    });
    setAttacks(prev => ({ ...prev, [uid]: iv.output }));
    setBusy(false);
    refresh();
  }

  async function setVerdict(uid: string, v: string) {
    setVerdicts(prev => ({ ...prev, [uid]: v }));
    await api.postMove(session.id, {
      round_id: "verdict",
      action: "assign_verdict",
      target_unit_id: uid,
      payload: { verdict: v },
    });
    refresh();
  }

  async function finish() {
    setBusy(true);
    const s = await api.complete(session.id);
    onChange(s);
    setBusy(false);
  }

  const allHaveVerdict = selected.length > 0 && selected.every(uid => verdicts[uid]);

  return (
    <div>
      <p className="muted">{material.payload.intro}</p>
      <div>
        {units.map(u => (
          <div
            key={u.id}
            className={"unit" + (selected.includes(u.id) ? " selected" : "")}
            onClick={() => toggleSelect(u.id, (u as any).dev_role || "pseudo_depth")}
          >
            {u.text}
            {selected.includes(u.id) && (
              <div onClick={e => e.stopPropagation()} style={{ marginTop: 8 }}>
                <label>Какую операцию делает фраза?</label>
                <input
                  value={ops[u.id] ?? ""}
                  onChange={e => setOps({ ...ops, [u.id]: e.target.value })}
                  placeholder="вводит различение / меняет масштаб / открывает отсутствующее…"
                />
                <div className="actions-bar">
                  <button disabled={!ops[u.id] || busy} onClick={() => proveAndAttack(u.id)}>
                    Доказать и вызвать прокурора
                  </button>
                </div>
                {attacks[u.id] && (
                  <div style={{ marginTop: 8, padding: 8, background: "var(--bg)", borderRadius: 4, fontSize: 13 }}>
                    <div className="llm-role-tag">prosecutor · атакует ваш выбор</div>
                    {attacks[u.id].attacks?.map((a: string, i: number) => (
                      <div key={i} style={{ marginTop: 4 }}>• {a}</div>
                    ))}
                    <div style={{ marginTop: 6, fontStyle: "italic", opacity: 0.85 }}>
                      ? {attacks[u.id].probe_question}
                    </div>
                  </div>
                )}
                {attacks[u.id] && (
                  <div style={{ marginTop: 8 }}>
                    <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>
                      Ваш ход после атаки. Это и есть защита — стоите вы на своей операции или признаёте слабость. Текстом отвечать прокурору не нужно.
                    </div>
                    <label>Вердикт под давлением</label>
                    <select value={verdicts[u.id] ?? ""} onChange={e => setVerdict(u.id, e.target.value)}>
                      <option value="">—</option>
                      {VERDICTS.map(v => (
                        <option key={v} value={v}>{v} — {VERDICT_MEANING[v]}</option>
                      ))}
                    </select>
                    {verdicts[u.id] && (
                      <div className="muted" style={{ fontSize: 11, marginTop: 4, fontStyle: "italic" }}>
                        зафиксировано как {verdicts[u.id]} · войдёт в profile.verdict_distribution
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="actions-bar">
        <button className="primary" disabled={!allHaveVerdict || busy} onClick={finish}>
          Завершить и собрать профиль
        </button>
        <span className="muted">выбрано {selected.length}/3</span>
      </div>
    </div>
  );
}

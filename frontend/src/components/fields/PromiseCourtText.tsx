import { useState } from "react";
import type { GameGenome, GameSession, Material } from "../../types";
import { api } from "../../api/client";

interface Props {
  genome: GameGenome;
  material: Material;
  session: GameSession;
  onChange: (s: GameSession) => void;
}

interface Form {
  owner?: string;
  deadline?: string;
  criterion?: string;
  fallback?: string;
}

export default function PromiseCourtText({ session, material, onChange }: Props) {
  const blocks = material.payload.blocks as { id: string; index: number; text: string; is_promise_candidate?: boolean }[];
  const [marked, setMarked] = useState<string[]>([]);
  const [forms, setForms] = useState<Record<string, Form>>({});
  const [verdicts, setVerdicts] = useState<Record<string, "accepted" | "sent_to_court">>({});
  const [busy, setBusy] = useState(false);

  function refresh() { api.getSession(session.id).then(onChange); }

  async function toggleMark(pid: string) {
    if (marked.includes(pid)) {
      setMarked(marked.filter(x => x !== pid));
      return;
    }
    if (marked.length >= 5) return;
    setMarked([...marked, pid]);
    await api.postMove(session.id, {
      round_id: "mark",
      action: "mark_promise",
      target_unit_id: pid,
      payload: {},
    });
    refresh();
  }

  async function saveForm(pid: string, patch: Partial<Form>) {
    const next = { ...(forms[pid] ?? {}), ...patch };
    setForms({ ...forms, [pid]: next });
    await api.postMove(session.id, {
      round_id: "fill",
      action: "fill_obligation_form",
      target_unit_id: pid,
      payload: next,
    });
  }

  async function decide(pid: string, verdict: "accepted" | "sent_to_court") {
    setVerdicts({ ...verdicts, [pid]: verdict });
    await api.postMove(session.id, {
      round_id: "verdict",
      action: verdict === "accepted" ? "accept_promise" : "send_to_court",
      target_unit_id: pid,
      payload: { verdict },
    });
    refresh();
  }

  async function finish() {
    setBusy(true);
    const s = await api.complete(session.id);
    onChange(s);
    setBusy(false);
  }

  function isComplete(pid: string): boolean {
    const f = forms[pid] ?? {};
    return Boolean(f.owner?.trim() && f.deadline?.trim() && f.criterion?.trim() && f.fallback?.trim());
  }

  const allDecided = marked.length > 0 && marked.every(pid => verdicts[pid]);

  return (
    <div>
      <p className="muted">{material.payload.intro}</p>
      {blocks.map(b => {
        const isMarked = marked.includes(b.id);
        return (
          <div
            key={b.id}
            className={"unit" + (isMarked ? " selected" : "")}
            onClick={() => toggleMark(b.id)}
            style={{ cursor: "pointer" }}
          >
            {b.text}
            {isMarked && (
              <div onClick={e => e.stopPropagation()} style={{ marginTop: 8 }}>
                <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>
                  Заполни 4 поля. Любое пустое = в суд.
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
                  <input placeholder="owner (имя)"
                         value={forms[b.id]?.owner ?? ""}
                         onChange={e => saveForm(b.id, { owner: e.target.value })} />
                  <input placeholder="deadline (дата)"
                         value={forms[b.id]?.deadline ?? ""}
                         onChange={e => saveForm(b.id, { deadline: e.target.value })} />
                  <input placeholder="criterion (как поймём)"
                         value={forms[b.id]?.criterion ?? ""}
                         onChange={e => saveForm(b.id, { criterion: e.target.value })} />
                  <input placeholder="fallback (если не выполнено)"
                         value={forms[b.id]?.fallback ?? ""}
                         onChange={e => saveForm(b.id, { fallback: e.target.value })} />
                </div>
                <div className="actions-bar" style={{ marginTop: 8 }}>
                  <button
                    onClick={() => decide(b.id, "accepted")}
                    disabled={!isComplete(b.id) || Boolean(verdicts[b.id])}
                    title={isComplete(b.id) ? "" : "не все поля заполнены — принять нельзя"}
                  >
                    Принять обещание
                  </button>
                  <button
                    onClick={() => decide(b.id, "sent_to_court")}
                    disabled={Boolean(verdicts[b.id])}
                  >
                    В суд
                  </button>
                  {verdicts[b.id] && (
                    <span className="muted" style={{ fontSize: 11, fontStyle: "italic" }}>
                      зафиксировано как {verdicts[b.id]}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
      <div className="actions-bar">
        <button className="primary" disabled={!allDecided || busy} onClick={finish}>
          Завершить и собрать профиль
        </button>
        <span className="muted">отмечено {marked.length}/5 · решено {Object.keys(verdicts).length}/{marked.length}</span>
      </div>
    </div>
  );
}

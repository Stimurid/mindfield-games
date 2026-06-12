import { useState } from "react";
import type { GameGenome, GameSession, Material } from "../../types";
import { api } from "../../api/client";

interface Props {
  genome: GameGenome;
  material: Material;
  session: GameSession;
  onChange: (s: GameSession) => void;
}

interface Variant { id: string; medium: string; context: string }

export default function MediumShiftPhrase({ genome, material, session, onChange }: Props) {
  const phrase = material.payload.phrase as string;
  const variants = material.payload.variants as Variant[];
  const [activeId, setActiveId] = useState(variants[0].id);
  const [actions, setActions] = useState<Record<string, string>>({});
  const [changed, setChanged] = useState("");
  const [alien, setAlien] = useState<{ literal_reading: string; things_i_cannot_see: string[] } | null>(null);
  const [repair, setRepair] = useState("");
  const [transferMedium, setTransferMedium] = useState("");
  const [transferPhrase, setTransferPhrase] = useState("");
  const [preserves, setPreserves] = useState(true);
  const [busy, setBusy] = useState(false);

  const active = variants.find(v => v.id === activeId)!;
  const ACTIONS = genome.phrase_actions ?? [];
  const MEDIUMS = genome.mediums ?? [];

  function refresh() { api.getSession(session.id).then(onChange); }

  async function assignAction(vid: string, act: string) {
    setActions(a => ({ ...a, [vid]: act }));
    const v = variants.find(x => x.id === vid)!;
    await api.postMove(session.id, {
      round_id: "first_read", action: "assign_phrase_action",
      target_unit_id: vid, payload: { phrase_action: act, medium: v.medium },
    });
    refresh();
  }

  async function compareShift() {
    if (!changed) return;
    await api.postMove(session.id, {
      round_id: "shift", action: "compare_medium_shift",
      payload: { from: variants[0].medium, to: active.medium, changed },
    });
    setBusy(true);
    const iv = await api.llmIntervene(session.id, "literal_alien", {
      phrase, medium: active.medium,
    });
    setAlien({
      literal_reading: iv.output.literal_reading,
      things_i_cannot_see: iv.output.things_i_cannot_see ?? [],
    });
    setBusy(false);
    refresh();
  }

  async function submitRepair() {
    if (!repair) return;
    await api.postMove(session.id, {
      round_id: "blindness", action: "repair_machine_reading",
      payload: { missed: repair },
    });
    refresh();
  }

  async function submitTransfer() {
    if (!transferMedium || !transferPhrase) return;
    await api.postMove(session.id, {
      round_id: "transfer", action: "transfer_phrase",
      payload: { target_medium: transferMedium, new_phrase: transferPhrase, preserves_action: preserves },
    });
    refresh();
  }

  async function finish() {
    setBusy(true);
    const s = await api.complete(session.id);
    onChange(s);
    setBusy(false);
  }

  const transfersDone = session.moves.some(m => m.action === "transfer_phrase");

  return (
    <div>
      <p className="muted">{material.payload.intro}</p>
      <div className="card">
        <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>«{phrase}»</div>
        <div className="medium-tabs">
          {variants.map(v => (
            <div key={v.id} className={"medium-tab" + (activeId === v.id ? " active" : "")} onClick={() => { setActiveId(v.id); setAlien(null); setChanged(""); }}>
              {v.medium}
            </div>
          ))}
        </div>
        <div className="muted" style={{ fontSize: 13 }}>{active.context}</div>
        <div style={{ marginTop: 10 }}>
          <label>Действие фразы в этом медиуме</label>
          <select value={actions[activeId] ?? ""} onChange={e => assignAction(activeId, e.target.value)}>
            <option value="">—</option>
            {ACTIONS.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
        {actions[activeId] && (
          <div style={{ marginTop: 10 }}>
            <label>Что изменилось при смене медиума? (адресат, риск, право ответа, темп…)</label>
            <input value={changed} onChange={e => setChanged(e.target.value)} placeholder="addressee shifted from peer to authority; refusal becomes alibi…" />
            <div className="actions-bar">
              <button disabled={!changed || busy} onClick={compareShift}>Зафиксировать сдвиг и вызвать literal_alien</button>
            </div>
          </div>
        )}
        {alien && (
          <div className="card" style={{ marginTop: 10, background: "var(--bg)" }}>
            <div className="llm-role-tag">literal_alien</div>
            <div><b>literal:</b> {alien.literal_reading}</div>
            <div style={{ marginTop: 4 }}><b>что я возможно не вижу:</b></div>
            <ul style={{ margin: "4px 0 0 16px" }}>
              {alien.things_i_cannot_see.map((x, i) => <li key={i}>{x}</li>)}
            </ul>
            <div style={{ marginTop: 8 }}>
              <label>Почини машинное чтение: что именно потерял alien?</label>
              <input value={repair} onChange={e => setRepair(e.target.value)} placeholder="pathos-reset, alibi, in-group code…" />
              <div className="actions-bar"><button onClick={submitRepair} disabled={!repair}>Сохранить починку</button></div>
            </div>
          </div>
        )}
      </div>

      <div className="card">
        <h4 style={{ marginTop: 0 }}>Перенос в новый медиум, сохраняя действие</h4>
        <label>Целевой медиум</label>
        <select value={transferMedium} onChange={e => setTransferMedium(e.target.value)}>
          <option value="">—</option>
          {MEDIUMS.filter(m => !variants.some(v => v.medium === m)).map(m => <option key={m} value={m}>{m}</option>)}
        </select>
        <label>Новая фраза (другие слова, тот же ход)</label>
        <input value={transferPhrase} onChange={e => setTransferPhrase(e.target.value)} placeholder="перепиши так, чтобы действие сохранилось" />
        <label><input type="checkbox" checked={preserves} onChange={e => setPreserves(e.target.checked)} style={{ width: "auto", marginRight: 6 }} /> сохраняет действие, не только слова</label>
        <div className="actions-bar">
          <button onClick={submitTransfer} disabled={!transferMedium || !transferPhrase}>Сохранить перенос</button>
        </div>
      </div>

      <div className="actions-bar">
        <button className="primary" disabled={!transfersDone || busy} onClick={finish}>Завершить</button>
      </div>
    </div>
  );
}

import { useMemo, useState } from "react";
import type { GameGenome, GameSession, Material } from "../../types";
import { api } from "../../api/client";

interface Props {
  genome: GameGenome;
  material: Material;
  session: GameSession;
  onChange: (s: GameSession) => void;
}

interface Card { id: string; text: string }
interface Zone { id: string; label: string; hint: string }

export default function CardSorting({ genome, material, session, onChange }: Props) {
  const cards = material.payload.cards as Card[];
  const zones = material.payload.zones as Zone[];
  const [placement, setPlacement] = useState<Record<string, string>>({}); // cardId -> zoneId
  const [advocacy, setAdvocacy] = useState<Record<string, { counterposition: string; pressure_question: string }>>({});
  const [criterion, setCriterion] = useState<Record<string, string>>({});
  const [tests, setTests] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);

  function refresh() { api.getSession(session.id).then(onChange); }

  async function place(cardId: string, zoneId: string) {
    const prev = placement[cardId];
    setPlacement(p => ({ ...p, [cardId]: zoneId }));
    const action = prev ? "revise_fate" : "sort_card";
    await api.postMove(session.id, {
      round_id: prev ? "revise" : "sort",
      action,
      target_unit_id: cardId,
      payload: { fate: zoneId, card_id: cardId, criterion: criterion[cardId] },
    });
    if (!prev) {
      // Trigger advocate on first sort of borderline cards (sample once per game on 1st 3 placements)
      const placed = Object.keys(placement).length;
      if (placed < 3) {
        const card = cards.find(c => c.id === cardId)!;
        const iv = await api.llmIntervene(session.id, "sprout_advocate", {
          card_text: card.text, fate: zoneId,
        });
        setAdvocacy(a => ({ ...a, [cardId]: { counterposition: iv.output.counterposition, pressure_question: iv.output.pressure_question } }));
      }
    }
    refresh();
  }

  async function saveIncubationTest(cardId: string) {
    if (!tests[cardId]) return;
    await api.postMove(session.id, {
      round_id: "incubate", action: "set_incubation_test", target_unit_id: cardId,
      payload: { card_id: cardId, test: tests[cardId] },
    });
    refresh();
  }

  async function finish() {
    setBusy(true);
    const s = await api.complete(session.id);
    onChange(s);
    setBusy(false);
  }

  const unsorted = cards.filter(c => !placement[c.id]);
  const incubated = cards.filter(c => placement[c.id] === "incubate");

  function onDragStart(e: React.DragEvent, cardId: string) {
    e.dataTransfer.setData("text/plain", cardId);
  }
  function onDropZone(e: React.DragEvent, zoneId: string) {
    e.preventDefault();
    const cardId = e.dataTransfer.getData("text/plain");
    if (cardId) place(cardId, zoneId);
    (e.currentTarget as HTMLElement).classList.remove("drag-over");
  }

  return (
    <div>
      <p className="muted">{material.payload.intro}</p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <div>
          <h4 style={{ marginTop: 0 }}>Стопка <span className="muted">({unsorted.length})</span></h4>
          <div style={{ maxHeight: 360, overflowY: "auto", border: "1px solid var(--border)", borderRadius: 4, padding: 8 }}>
            {unsorted.map(c => (
              <div key={c.id} className="sort-card" draggable onDragStart={e => onDragStart(e, c.id)}>
                {c.text}
              </div>
            ))}
            {unsorted.length === 0 && <div className="muted" style={{ padding: 8 }}>пусто</div>}
          </div>
        </div>
        <div className="card-board">
          {zones.map(z => (
            <div
              key={z.id}
              className="zone"
              onDragOver={e => { e.preventDefault(); (e.currentTarget as HTMLElement).classList.add("drag-over"); }}
              onDragLeave={e => (e.currentTarget as HTMLElement).classList.remove("drag-over")}
              onDrop={e => onDropZone(e, z.id)}
            >
              <h4>{z.label} <span className="muted" style={{ fontWeight: 400, textTransform: "none" }}>· {z.hint}</span></h4>
              {cards.filter(c => placement[c.id] === z.id).map(c => (
                <div key={c.id} className="sort-card" draggable onDragStart={e => onDragStart(e, c.id)}>
                  <div>{c.text}</div>
                  {advocacy[c.id] && (
                    <div style={{ marginTop: 6, padding: 6, background: "var(--bg-2)", borderRadius: 3, fontSize: 12 }}>
                      <div className="llm-role-tag">sprout_advocate</div>
                      <div>{advocacy[c.id].counterposition}</div>
                      <div style={{ fontStyle: "italic", marginTop: 4 }}>{advocacy[c.id].pressure_question}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      {incubated.length > 0 && (
        <div className="card" style={{ marginTop: 16 }}>
          <h4 style={{ marginTop: 0 }}>Критерии проверки для ростков</h4>
          {incubated.slice(0, 2).map(c => (
            <div key={c.id} style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 13, marginBottom: 4 }}>{c.text}</div>
              <input
                value={tests[c.id] ?? ""}
                onChange={e => setTests({ ...tests, [c.id]: e.target.value })}
                onBlur={() => saveIncubationTest(c.id)}
                placeholder="срок и способ проверки — что считать ростом, что гнилью"
              />
            </div>
          ))}
        </div>
      )}

      <div className="actions-bar">
        <button className="primary" disabled={Object.keys(placement).length < 5 || busy} onClick={finish}>
          Завершить (нужно ≥5 карточек)
        </button>
        <span className="muted">распределено {Object.keys(placement).length}/{cards.length}</span>
      </div>
    </div>
  );
}

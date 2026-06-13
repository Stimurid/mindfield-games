import { useEffect, useState } from "react";
import { api } from "../api/client";

interface Props {
  entryId: string;
  onDone?: () => void;
}

const BANKS = ["field", "object", "action", "llm_role", "crisis", "trace", "mutation", "degradation"] as const;
const BANK_LABEL: Record<string, string> = {
  field: "Поле",
  object: "Объект",
  action: "Действие",
  llm_role: "LLM-роль",
  crisis: "Кризис",
  trace: "След",
  mutation: "Мутация",
  degradation: "Деградация (избегать)",
};

export default function TriagePanel({ entryId, onDone }: Props) {
  const [fates, setFates] = useState<{ fate: string; label: string }[] | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [bank, setBank] = useState<string>("action");
  const [organName, setOrganName] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.triageFates().then(setFates).catch(() => {});
    api.triageEntry(entryId).then(setHistory).catch(() => {});
  }, [entryId]);

  async function submit() {
    if (!selected) return;
    setBusy(true);
    setErr(null);
    try {
      const payload: any = { fate: selected };
      if (note.trim()) payload.note = note.trim();
      if (selected === "extract_organ") {
        if (!organName.trim()) throw new Error("укажи имя органа");
        payload.organ_bank = bank;
        payload.organ_name = organName.trim();
      }
      const v = await api.assignFate(entryId, payload);
      setHistory([v, ...history]);
      setSelected(null);
      setNote("");
      setOrganName("");
      onDone?.();
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally {
      setBusy(false);
    }
  }

  if (!fates) return null;

  return (
    <div className="card" style={{ marginTop: 12 }}>
      <div className="muted" style={{ fontSize: 12, marginBottom: 6 }}>
        Триаж. Назначь судьбу: одно из 9 решений из §4. Если орган стоит сохранить — извлеки его в банк.
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
        {fates.map(f => (
          <button
            key={f.fate}
            onClick={() => setSelected(f.fate)}
            style={{
              fontSize: 12, padding: "4px 8px",
              background: selected === f.fate ? "rgba(80,160,80,0.25)" : "var(--bg)",
              border: selected === f.fate ? "1px solid var(--accent)" : "1px solid var(--border)",
            }}
          >
            {f.label}
          </button>
        ))}
      </div>

      {selected && (
        <div style={{ marginTop: 10 }}>
          <input
            value={note}
            onChange={e => setNote(e.target.value)}
            placeholder="комментарий (опционально)"
          />
          {selected === "extract_organ" && (
            <div style={{ marginTop: 8, display: "grid", gridTemplateColumns: "1fr 2fr", gap: 8 }}>
              <select value={bank} onChange={e => setBank(e.target.value)}>
                {BANKS.map(b => <option key={b} value={b}>{BANK_LABEL[b]}</option>)}
              </select>
              <input
                value={organName}
                onChange={e => setOrganName(e.target.value)}
                placeholder="имя органа (что переносим в банк)"
              />
            </div>
          )}
          <div className="actions-bar" style={{ marginTop: 8 }}>
            <button className="primary" onClick={submit} disabled={busy}>
              {busy ? "Сохраняю…" : "Зафиксировать судьбу"}
            </button>
            <button onClick={() => setSelected(null)}>Отмена</button>
          </div>
          {err && <div style={{ color: "var(--warn)", fontSize: 12, marginTop: 6 }}>{err}</div>}
        </div>
      )}

      {history.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <div className="muted" style={{ fontSize: 11 }}>История решений ({history.length}):</div>
          {history.map(h => (
            <div key={h.id} style={{ fontSize: 12, marginTop: 4 }}>
              <span className="kbd">{h.fate}</span>
              {h.extracted_organ_id && <span className="muted" style={{ marginLeft: 6 }}>→ орган извлечён</span>}
              {h.note && <span style={{ marginLeft: 8, fontStyle: "italic" }}>{h.note}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

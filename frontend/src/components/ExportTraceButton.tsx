import { api } from "../api/client";
import type { GameSession } from "../types";

export default function ExportTraceButton({ session }: { session: GameSession }) {
  async function grab() {
    const md = await api.exportMd(session.id);
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `mindfield-${session.game_id}-${session.id.slice(0, 8)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }
  async function copy() {
    const md = await api.exportMd(session.id);
    try {
      await navigator.clipboard.writeText(md);
      alert("Trace .md скопирован в буфер обмена");
    } catch {
      alert(md.slice(0, 4000));
    }
  }
  return (
    <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
      <button onClick={grab} title="Скачать .md с текущим следом">⤓ .md</button>
      <button onClick={copy} title="Скопировать .md в буфер">⧉ copy</button>
    </div>
  );
}

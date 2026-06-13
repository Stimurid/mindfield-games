import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

const STAGE_PROMPTS: Record<string, { stage: string; prompt: string; placeholder?: string }[]> = {
  after_triage: [
    { stage: "after_triage", prompt: "Какую судьбу ты назначил карточке и почему?", placeholder: "одно-два предложения" },
  ],
  after_game_1: [
    { stage: "after_game_1", prompt: "Что ты думал, что делаешь?", placeholder: "своими словами" },
    { stage: "after_game_1", prompt: "Что игра заставила тебя сделать, чего обычный чат с ChatGPT не заставляет?" },
    { stage: "after_game_1", prompt: "LLM был игровым органом, ассистентом или просто шумом? Назови момент." },
    { stage: "after_game_1", prompt: "Что было непонятно?" },
  ],
  after_profile: [
    { stage: "after_profile", prompt: "Какую слепоту/паттерн назвал тебе профиль?" },
    { stage: "after_profile", prompt: "Это специфично, обобщённо, неверно или полезно? Процитируй одну фразу, которая попала или промахнулась." },
  ],
  after_replay: [
    { stage: "after_replay", prompt: "Второй материал ЦЕЛИЛСЯ в детектированную слабость, или это просто другой текст?" },
    { stage: "after_replay", prompt: "Что изменилось в твоём действии на втором раунде?" },
  ],
  final: [
    { stage: "final", prompt: "Назови одну операцию, которую ты можешь заметить вне приложения." },
  ],
};

const VERDICTS = [
  { id: "software_only",        label: "software_only — это просто работающий софт" },
  { id: "profile_recognition",  label: "profile_recognition — профиль попал в реальный паттерн" },
  { id: "replay_targeting",     label: "replay_targeting — второй раунд бил по детектированной слабости" },
  { id: "transfer_candidate",   label: "transfer_candidate — есть шанс, что операция выйдет вне приложения" },
  { id: "unclear",              label: "unclear — пока не могу сказать" },
];

function makeShareLink(token: string): string {
  return `${window.location.origin}/playtest/followup/${token}`;
}

export default function PlaytestFullCycle() {
  const STORAGE_KEY = "mindfield.playtest_run_id";
  const [run, setRun] = useState<any | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [verdict, setVerdict] = useState<string>("unclear");
  const [exported, setExported] = useState<string | null>(null);

  useEffect(() => {
    const rid = localStorage.getItem(STORAGE_KEY);
    if (rid) api.playtestGet(rid).then(setRun).catch(() => localStorage.removeItem(STORAGE_KEY));
  }, []);

  async function start(mode: string) {
    setBusy(true); setErr(null);
    try {
      const r = await api.playtestStart({ mode });
      setRun(r);
      localStorage.setItem(STORAGE_KEY, r.id);
    } catch (e: any) { setErr(String(e?.message ?? e)); }
    finally { setBusy(false); }
  }

  async function submitStage(stage: string) {
    if (!run) return;
    const prompts = STAGE_PROMPTS[stage] ?? [];
    setBusy(true); setErr(null);
    try {
      for (const p of prompts) {
        const key = `${stage}::${p.prompt}`;
        const ans = (answers[key] ?? "").trim();
        if (!ans) continue;
        await api.playtestReflect(run.id, stage, p.prompt, ans);
      }
      const refreshed = await api.playtestGet(run.id);
      setRun(refreshed);
    } catch (e: any) { setErr(String(e?.message ?? e)); }
    finally { setBusy(false); }
  }

  async function complete() {
    if (!run) return;
    setBusy(true); setErr(null);
    try {
      const r = await api.playtestComplete(run.id, verdict);
      setRun(r);
    } catch (e: any) { setErr(String(e?.message ?? e)); }
    finally { setBusy(false); }
  }

  async function doExport() {
    if (!run) return;
    setBusy(true); setErr(null);
    try {
      const x = await api.playtestExport(run.id);
      setExported(x.body);
      const blob = new Blob([x.body], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `mindfield-playtest-${run.id.slice(0,8)}.md`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) { setErr(String(e?.message ?? e)); }
    finally { setBusy(false); }
  }

  function reset() {
    localStorage.removeItem(STORAGE_KEY);
    setRun(null);
    setAnswers({});
    setExported(null);
  }

  function isStageDone(stage: string): boolean {
    if (!run) return false;
    return (run.reflections ?? []).some((r: any) => r.stage === stage);
  }

  if (!run) {
    return (
      <div className="app">
        <div className="header">
          <Link to="/">← все игры</Link>
          <span className="muted">Full-cycle playtest harness</span>
        </div>
        <h2>Full-cycle playtest</h2>
        <p style={{ fontSize: 14, lineHeight: 1.6 }}>
          Это не игра — это инструмент сбора доказательств. Ты пройдёшь триаж, одну игру,
          профиль, replay, ещё одну игру. После каждого шага — короткая рефлексия. В конце
          получишь .md экспорт и ссылку, по которой через ~24 часа надо вернуться.
        </p>
        <p className="muted" style={{ fontSize: 13 }}>
          Backend trace сам по себе НЕ доказывает психотехнический сигнал. Поэтому
          рефлексии — обязательная часть.
        </p>
        {err && <div className="card" style={{ color: "var(--warn)" }}>{err}</div>}
        <div className="actions-bar" style={{ marginTop: 16 }}>
          <button className="primary" onClick={() => start("self_test")} disabled={busy}>Начать как self-test</button>
          <button onClick={() => start("remote_test")} disabled={busy}>Начать как remote_test</button>
          <button onClick={() => start("moderated")} disabled={busy}>Начать как moderated</button>
        </div>
      </div>
    );
  }

  const followupUrl = run.followup ? makeShareLink(run.followup.token) : "";
  const showCompleteBlock = !run.completed_at && Object.keys(STAGE_PROMPTS).every(s => s === "final" || isStageDone(s));

  return (
    <div className="app">
      <div className="header" style={{ flexWrap: "wrap", gap: 8 }}>
        <Link to="/">← все игры</Link>
        <span className="muted">Playtest run · {run.id.slice(0,8)} · {run.mode}</span>
        {run.completed_at && <span className="kbd" style={{ background: "rgba(80,160,80,0.25)" }}>completed</span>}
      </div>

      <h2>Full-cycle playtest <span className="muted" style={{ fontSize: 14 }}>· {run.final_verdict ? `verdict: ${run.final_verdict}` : "in progress"}</span></h2>

      {err && <div className="card" style={{ color: "var(--warn)" }}>{err}</div>}

      <div className="card" style={{ marginTop: 8 }}>
        <h3 style={{ marginTop: 0 }}>1. Триаж одной карточки</h3>
        <div className="muted" style={{ fontSize: 12 }}>
          Открой <Link to="/triage">/triage</Link>. Выбери одну сырую карточку. Назначь судьбу
          (одну из 9). Если выбрал «извлечь орган» — обрати внимание на банк.
        </div>
        {renderStageReflection("after_triage")}
      </div>

      <div className="card" style={{ marginTop: 8 }}>
        <h3 style={{ marginTop: 0 }}>2. Первая сессия</h3>
        <div className="muted" style={{ fontSize: 12 }}>
          Открой <Link to="/">любой жанр</Link>. Игра автоматически возьмёт реальный сид. Сыграй сессию до конца.
        </div>
        {renderStageReflection("after_game_1")}
      </div>

      <div className="card" style={{ marginTop: 8 }}>
        <h3 style={{ marginTop: 0 }}>3. Профиль и Operator</h3>
        <div className="muted" style={{ fontSize: 12 }}>
          После завершения игры — страница профиля. Прочти размерности и replay-директиву.
          Затем зайди в <Link to="/operator">/operator</Link>.
        </div>
        {renderStageReflection("after_profile")}
      </div>

      <div className="card" style={{ marginTop: 8 }}>
        <h3 style={{ marginTop: 0 }}>4. Replay — мутированный раунд</h3>
        <div className="muted" style={{ fontSize: 12 }}>
          На странице профиля нажми «Сыграть мутировавший раунд». Сыграй второй раунд.
        </div>
        {renderStageReflection("after_replay")}
      </div>

      <div className="card" style={{ marginTop: 8 }}>
        <h3 style={{ marginTop: 0 }}>5. Финальная рефлексия и вердикт</h3>
        {renderStageReflection("final")}
        <div style={{ marginTop: 12 }}>
          <div className="muted" style={{ fontSize: 12 }}>текущий вердикт:</div>
          <select value={verdict} onChange={e => setVerdict(e.target.value)} style={{ width: "100%", marginTop: 4 }}>
            {VERDICTS.map(v => <option key={v.id} value={v.id}>{v.label}</option>)}
          </select>
        </div>
        {!run.completed_at && (
          <div className="actions-bar" style={{ marginTop: 12 }}>
            <button className="primary" disabled={!showCompleteBlock || busy} onClick={complete}>
              Завершить run
            </button>
            {!showCompleteBlock && <span className="muted" style={{ fontSize: 11 }}>заполни рефлексии этапов 1-4</span>}
          </div>
        )}
      </div>

      {run.completed_at && (
        <div className="card" style={{ marginTop: 12, borderLeft: "3px solid var(--accent)" }}>
          <h3 style={{ marginTop: 0 }}>Готово · 24h follow-up</h3>
          <p className="muted" style={{ fontSize: 12 }}>
            Сохрани и/или перешли эту ссылку себе на почту/в Telegram. Через ~24 часа открой её
            и заполни короткий чек-лист: появился ли сигнал ВНЕ приложения.
          </p>
          <div style={{ background: "var(--bg)", padding: 8, borderRadius: 4, fontFamily: "monospace", fontSize: 12, wordBreak: "break-all" }}>
            {followupUrl}
          </div>
          <div className="actions-bar" style={{ marginTop: 8 }}>
            <button onClick={() => navigator.clipboard.writeText(followupUrl)}>Скопировать ссылку</button>
            <button onClick={doExport}>Скачать .md</button>
            <button onClick={reset}>Новый run</button>
          </div>
          {exported && (
            <details style={{ marginTop: 12 }}>
              <summary className="muted" style={{ fontSize: 12 }}>посмотреть .md</summary>
              <pre style={{ fontSize: 11, whiteSpace: "pre-wrap" }}>{exported}</pre>
            </details>
          )}
        </div>
      )}
    </div>
  );

  function renderStageReflection(stage: string) {
    const prompts = STAGE_PROMPTS[stage] ?? [];
    const done = isStageDone(stage);
    return (
      <div style={{ marginTop: 8 }}>
        {prompts.map(p => {
          const key = `${stage}::${p.prompt}`;
          return (
            <div key={key} style={{ marginTop: 8 }}>
              <label className="muted" style={{ fontSize: 12 }}>{p.prompt}</label>
              <textarea
                value={answers[key] ?? ""}
                onChange={e => setAnswers({ ...answers, [key]: e.target.value })}
                placeholder={p.placeholder ?? "ответ"}
                style={{ width: "100%", minHeight: 60, marginTop: 4 }}
                disabled={done && !!run.completed_at}
              />
            </div>
          );
        })}
        <div className="actions-bar" style={{ marginTop: 6 }}>
          <button onClick={() => submitStage(stage)} disabled={busy || (done && !!run.completed_at)}>
            {done ? "Дописать рефлексию" : "Сохранить рефлексию"}
          </button>
          {done && <span className="muted" style={{ fontSize: 11 }}>✓ записана</span>}
        </div>
      </div>
    );
  }
}

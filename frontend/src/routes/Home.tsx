import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { GameGenome } from "../types";

interface Counts {
  games: number | null;
  organs: number | null;
  organBanks: number | null;
  corpus: number | null;
  corpusSections: number | null;
  fates: number | null;
  // Sub-counts for the orientation map.
  corpusByKind: Record<string, number>;
}

const STARTER_GAME = "false_click";

export default function Home() {
  const [games, setGames] = useState<GameGenome[] | null>(null);
  const [counts, setCounts] = useState<Counts>({
    games: null, organs: null, organBanks: null, corpus: null,
    corpusSections: null, fates: null, corpusByKind: {},
  });
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.listGames().then(setGames).catch(e => setErr(String(e)));

    // Fetch all numbers in parallel; partial failure is fine.
    Promise.allSettled([
      api.librarySections(),
      api.configBanks(),
      api.configOrgans(),
      api.triageFates(),
    ]).then(results => {
      const [secsR, banksR, organsR, fatesR] = results;
      const sections = secsR.status === "fulfilled" ? secsR.value : [];
      const banks = banksR.status === "fulfilled" ? banksR.value : [];
      const organs = organsR.status === "fulfilled" ? organsR.value : [];
      const fates = fatesR.status === "fulfilled" ? fatesR.value : [];

      const byKind: Record<string, number> = {};
      let corpusTotal = 0;
      for (const s of sections) {
        byKind[s.kind] = s.count;
        corpusTotal += s.count;
      }

      setCounts({
        games: null,         // games count comes from listGames below
        organs: organs.length || null,
        organBanks: banks.length || null,
        corpus: corpusTotal || null,
        corpusSections: sections.length || null,
        fates: fates.length || null,
        corpusByKind: byKind,
      });
    });
  }, []);

  // Keep the games count in sync with the loaded genome list.
  const gamesCount = games?.length ?? counts.games;

  const starter = useMemo(() => games?.find(g => g.id === STARTER_GAME), [games]);

  return (
    <div className="app">
      <div className="header">
        <h1>Mindfield Games <span className="muted">— Operator Calibration Pack</span></h1>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <Link to="/research" className="kbd" style={{ textDecoration: "none", background: "rgba(80,160,80,0.18)" }}>Researcher →</Link>
          <Link to="/playtest/full-cycle" className="kbd" style={{ textDecoration: "none", background: "rgba(160,120,80,0.18)" }}>Playtest →</Link>
          <Link to="/library" className="kbd" style={{ textDecoration: "none" }}>Library →</Link>
          <Link to="/triage" className="kbd" style={{ textDecoration: "none" }}>Triage →</Link>
          <Link to="/configurator" className="kbd" style={{ textDecoration: "none" }}>Configurator →</Link>
          <Link to="/operator" className="kbd" style={{ textDecoration: "none" }}>Operator Profile →</Link>
          <Link to="/admin/materials" className="kbd" style={{ textDecoration: "none", opacity: 0.6 }}>Admin</Link>
        </div>
      </div>

      {/* ── Hero ────────────────────────────────────────────────────────── */}
      <div className="card" style={{ borderLeft: "3px solid var(--accent)" }}>
        <p style={{ marginTop: 0, lineHeight: 1.55 }}>
          Это <b>полевой тренажёр различения</b>, а не игра в обычном смысле. LLM здесь не помощник
          и не оракул — это игровой орган: <i>прокурор</i> атакует твой выбор, <i>шпаклёвщик</i>
          подбрасывает гладкие имитации операции, <i>адвокат ростка</i> защищает то, что ты вырезаешь,
          <i>литералист-чужой</i> читает фразы плоско и теряет регистр.
        </p>
        <p style={{ marginTop: 8, marginBottom: 0, lineHeight: 1.55, fontSize: 14 }}>
          Игрок формирует операцию различения; исследователь собирает свою игру и записывает гипотезу;
          модератор запускает протоколированный playtest. Результат — не очки, а <b>качественный
          Operator Profile</b>: именованные слепоты и связки между жанрами.
        </p>
      </div>

      {/* ── Три входа по аудиториям ─────────────────────────────────────── */}
      <div
        style={{
          marginTop: 12,
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 8,
        }}
      >
        <Link to={`/play/${STARTER_GAME}`} style={{ textDecoration: "none", color: "inherit" }}>
          <div className="card" style={{ height: "100%" }}>
            <div className="muted" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5 }}>
              для игрока
            </div>
            <h3 style={{ margin: "4px 0" }}>Сыграть одну сессию</h3>
            <div className="muted" style={{ fontSize: 12 }}>
              Начни с <b>{starter?.short_title ?? "False Click"}</b> — 10 минут. Реальный материал,
              живая модель.
            </div>
          </div>
        </Link>

        <Link to="/research" style={{ textDecoration: "none", color: "inherit" }}>
          <div className="card" style={{ height: "100%" }}>
            <div className="muted" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5 }}>
              для исследователя
            </div>
            <h3 style={{ margin: "4px 0" }}>Разобраться в инструменте</h3>
            <div className="muted" style={{ fontSize: 12 }}>
              Что это, чего тут НЕТ, как записать гипотезу и атаковать её органами.
            </div>
          </div>
        </Link>

        <Link to="/configurator" style={{ textDecoration: "none", color: "inherit" }}>
          <div className="card" style={{ height: "100%" }}>
            <div className="muted" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5 }}>
              для дизайнера
            </div>
            <h3 style={{ margin: "4px 0" }}>Собрать свою игру</h3>
            <div className="muted" style={{ fontSize: 12 }}>
              8 банков органов · GameWeaver валидирует черновик · промотируй и играй сам.
            </div>
          </div>
        </Link>
      </div>

      {/* ── Карта: где что лежит ────────────────────────────────────────── */}
      <h3 style={{ marginTop: 24, marginBottom: 6 }}>Карта инструмента</h3>
      <div className="muted" style={{ fontSize: 12, marginBottom: 8 }}>
        Это не игра — это инструмент. Шесть рабочих поверхностей. Числа живые, из БД.
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: 12,
        }}
      >
        <MapCell
          title="Корпус"
          count={counts.corpus}
          unit="записей"
          to="/library"
          body={
            counts.corpusByKind ? (
              <>
                {countLine(counts.corpusByKind, "attractor",     "аттракторов")}
                {countLine(counts.corpusByKind, "r_root",        "R-корней")}
                {countLine(counts.corpusByKind, "breed",         "пород")}
                {countLine(counts.corpusByKind, "chimera",       "химер")}
                {countLine(counts.corpusByKind, "source_card",   "сырых карточек")}
                {countLine(counts.corpusByKind, "micro_aspect",  "аспектов пород")}
                {countLine(counts.corpusByKind, "phase_doc",     "документов фаз разработки")}
              </>
            ) : null
          }
          cta="Читать · искать · вызывать органы над записью"
        />

        <MapCell
          title="Банки органов"
          count={counts.organs}
          unit="органов"
          to="/configurator"
          body={
            <div className="muted" style={{ fontSize: 12 }}>
              {counts.organBanks ? `${counts.organBanks} банков: ` : "8 банков: "}
              поле, объект, действие, LLM-роль, кризис, след, мутация, деградация.
              Растут от триажа и химер.
            </div>
          }
          cta="Открыть конфигуратор"
        />

        <MapCell
          title="Конфигуратор + GameWeaver"
          count={null}
          unit=""
          to="/configurator"
          body={
            <div className="muted" style={{ fontSize: 12 }}>
              Имя, функция, playable verb, стадия зрелости + чипы из банков.
              GameWeaver атакует черновик. Промотируешь → играешь.
            </div>
          }
          cta="Собрать игру"
        />

        <MapCell
          title="Триаж сырого материала"
          count={counts.fates}
          unit="судеб"
          to="/triage"
          body={
            <div className="muted" style={{ fontSize: 12 }}>
              Похоронить · извлечь орган · оставить семенем · сжать до упражнения ·
              поднять до игры · скрестить · вырастить породу · отложить · запретить.
              «Извлечь орган» наращивает банк.
            </div>
          }
          cta="Открыть очередь"
        />

        <MapCell
          title="Гипотезы исследователя"
          count={null}
          unit=""
          to="/research"
          body={
            <div className="muted" style={{ fontSize: 12 }}>
              Записать утверждение, атаковать его 4 органами, привязать к черновику игры,
              превратить в playable форму. Один клик = один ход роли, не чат.
            </div>
          }
          cta="Открыть верстак"
        />

        <MapCell
          title="Профиль и playtest"
          count={gamesCount}
          unit="жанров"
          to="/operator"
          body={
            <div className="muted" style={{ fontSize: 12 }}>
              Качественный профиль по сессиям — слепоты, склонности, названные связки между
              жанрами. Playtest harness фиксирует рефлексии и 24h follow-up для переноса операции.
            </div>
          }
          cta="Operator Profile · Playtest"
        />
      </div>

      {/* ── Правила сборки: честный код-пойнтер ─────────────────────────── */}
      <div className="card" style={{ marginTop: 12, fontSize: 12 }}>
        <b>Правила сборки и онтология</b> — стадии зрелости (0–5), словарь судеб триажа,
        маппинг каноническая роль → runtime-роль, словарь cross-patterns профиля, дефолты
        банков — сейчас определяются в коде:{" "}
        <code>backend/app/services/organ_seed.py</code>,{" "}
        <code>backend/app/services/genome_promote.py</code>,{" "}
        <code>backend/app/services/operator_profile.py</code>,{" "}
        <code>backend/app/api/triage.py</code>.{" "}
        UI для их редактирования — отдельный заход. Сейчас правки только через PR.
      </div>

      {/* ── Список 12 жанров ────────────────────────────────────────────── */}
      <h3 style={{ marginTop: 24, marginBottom: 6 }}>
        Игры <span className="muted" style={{ fontSize: 13, fontWeight: "normal" }}>
          · {gamesCount ?? "…"} канонических жанров
        </span>
      </h3>
      <div className="muted" style={{ fontSize: 12, marginBottom: 8 }}>
        Реальный материал берётся по умолчанию. LLM-модель — gpt-4.1-mini для большинства,
        grok-4-0709 для register_sapper и assistant_as_foreign.
      </div>

      {err && <div className="card" style={{ color: "var(--warn)" }}>API error: {err}</div>}
      {!games && !err && <div className="muted">Loading…</div>}

      {games?.map(g => (
        <Link key={g.id} to={`/play/${g.id}`} style={{ textDecoration: "none", color: "inherit" }}>
          <div className="card game-card">
            <h3 style={{ margin: "0 0 4px" }}>
              {g.title}
              {g.id === STARTER_GAME && (
                <span className="kbd" style={{ marginLeft: 8, background: "rgba(80,160,80,0.2)", fontSize: 11 }}>
                  starter
                </span>
              )}
            </h3>
            <div className="muted" style={{ fontSize: 13 }}>{g.function}</div>
          </div>
        </Link>
      ))}

      <div style={{ marginTop: 24, fontSize: 11, color: "var(--fg-dim)" }}>
        Под капотом: FastAPI + SQLite + Vite/React. LLM через 302.ai. 12 жанров,
        130 канонических органов, 4720 записей корпуса, 40 химерных ячеек. RC-0 заморозка
        нарушена два раза: для researcher workbench и для playtest harness. Подробнее —
        в <code>docs/releases/MINDFIELD_RC0_FREEZE_2026-06-13.md</code>.
      </div>
    </div>
  );
}

function MapCell({
  title, count, unit, to, body, cta,
}: {
  title: string;
  count: number | null;
  unit: string;
  to: string;
  body: React.ReactNode;
  cta: string;
}) {
  return (
    <Link to={to} style={{ textDecoration: "none", color: "inherit" }}>
      <div className="card" style={{ height: "100%", display: "flex", flexDirection: "column" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
          <h4 style={{ margin: 0 }}>{title}</h4>
          {count !== null && (
            <span className="kbd" style={{ fontSize: 11 }}>{count} {unit}</span>
          )}
        </div>
        <div style={{ marginTop: 6, flex: 1, fontSize: 12, lineHeight: 1.5 }}>{body}</div>
        <div className="muted" style={{ marginTop: 8, fontSize: 11, fontStyle: "italic" }}>
          {cta} →
        </div>
      </div>
    </Link>
  );
}

function countLine(by: Record<string, number>, kind: string, label: string) {
  const v = by[kind];
  if (!v) return null;
  return (
    <div className="muted" style={{ fontSize: 12 }}>
      · {v} {label}
    </div>
  );
}

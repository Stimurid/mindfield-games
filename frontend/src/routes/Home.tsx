import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { GameGenome } from "../types";
import { useT } from "../i18n";
import LanguageSwitcher from "../components/LanguageSwitcher";

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
  const t = useT();
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
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <LanguageSwitcher />
          <Link to="/research" className="kbd" style={{ textDecoration: "none", background: "rgba(80,160,80,0.18)" }}>{t("Researcher", "Researcher")} →</Link>
          <Link to="/playtest/full-cycle" className="kbd" style={{ textDecoration: "none", background: "rgba(160,120,80,0.18)" }}>{t("Playtest", "Playtest")} →</Link>
          <Link to="/library" className="kbd" style={{ textDecoration: "none" }}>{t("Library", "Library")} →</Link>
          <Link to="/triage" className="kbd" style={{ textDecoration: "none" }}>{t("Triage", "Triage")} →</Link>
          <Link to="/configurator" className="kbd" style={{ textDecoration: "none" }}>{t("Configurator", "Configurator")} →</Link>
          <Link to="/operator" className="kbd" style={{ textDecoration: "none" }}>{t("Operator Profile", "Operator Profile")} →</Link>
          <Link to="/admin/materials" className="kbd" style={{ textDecoration: "none", opacity: 0.6 }}>Admin</Link>
          <Link to="/admin/ontology" className="kbd" style={{ textDecoration: "none", opacity: 0.6 }}>Ontology</Link>
        </div>
      </div>

      {/* ── Hero ────────────────────────────────────────────────────────── */}
      <div className="card" style={{ borderLeft: "3px solid var(--accent)" }}>
        <p style={{ marginTop: 0, lineHeight: 1.55 }}>
          {t(
            "Это ",
            "This is a ",
          )}
          <b>{t("полевой тренажёр различения", "field trainer of discrimination")}</b>
          {t(
            ", а не игра в обычном смысле. LLM здесь не помощник и не оракул — это игровой орган: ",
            ", not a game in the usual sense. The LLM here is not an assistant and not an oracle — it is a game-organ: ",
          )}
          <i>{t("прокурор", "prosecutor")}</i>
          {t(" атакует твой выбор, ", " attacks your choice, ")}
          <i>{t("шпаклёвщик", "spackler")}</i>
          {t(
            " подбрасывает гладкие имитации операции, ",
            " plants smooth imitations of operation, ",
          )}
          <i>{t("адвокат ростка", "sprout advocate")}</i>
          {t(
            " защищает то, что ты вырезаешь, ",
            " defends what you cut, ",
          )}
          <i>{t("литералист-чужой", "literal alien")}</i>
          {t(
            " читает фразы плоско и теряет регистр.",
            " reads phrases flat and loses register.",
          )}
        </p>
        <p style={{ marginTop: 8, marginBottom: 0, lineHeight: 1.55, fontSize: 14 }}>
          {t(
            "Игрок формирует операцию различения; исследователь собирает свою игру и записывает гипотезу; модератор запускает протоколированный playtest. Результат — не очки, а ",
            "The player forms an operation of discrimination; the researcher assembles their own game and records a hypothesis; the moderator runs a protocolled playtest. The result is not points but a ",
          )}
          <b>{t("качественный Operator Profile", "qualitative Operator Profile")}</b>
          {t(
            ": именованные слепоты и связки между жанрами.",
            ": named blindnesses and cross-genre connections.",
          )}
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
              {t("для игрока", "for the player")}
            </div>
            <h3 style={{ margin: "4px 0" }}>{t("Сыграть одну сессию", "Play one session")}</h3>
            <div className="muted" style={{ fontSize: 12 }}>
              {t("Начни с ", "Start with ")}<b>{starter?.short_title ?? "False Click"}</b>
              {t(" — 10 минут. Реальный материал, живая модель.",
                 " — 10 minutes. Real material, live model.")}
            </div>
          </div>
        </Link>

        <Link to="/research" style={{ textDecoration: "none", color: "inherit" }}>
          <div className="card" style={{ height: "100%" }}>
            <div className="muted" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5 }}>
              {t("для исследователя", "for the researcher")}
            </div>
            <h3 style={{ margin: "4px 0" }}>{t("Разобраться в инструменте", "Understand the tool")}</h3>
            <div className="muted" style={{ fontSize: 12 }}>
              {t("Что это, чего тут НЕТ, как записать гипотезу и атаковать её органами.",
                 "What this is, what is NOT here, how to record a hypothesis and attack it with organs.")}
            </div>
          </div>
        </Link>

        <Link to="/configurator" style={{ textDecoration: "none", color: "inherit" }}>
          <div className="card" style={{ height: "100%" }}>
            <div className="muted" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5 }}>
              {t("для дизайнера", "for the designer")}
            </div>
            <h3 style={{ margin: "4px 0" }}>{t("Собрать свою игру", "Assemble your own game")}</h3>
            <div className="muted" style={{ fontSize: 12 }}>
              {t("8 банков органов · GameWeaver валидирует черновик · промотируй и играй сам.",
                 "8 organ banks · GameWeaver validates the draft · promote and play.")}
            </div>
          </div>
        </Link>
      </div>

      {/* ── Карта: где что лежит ────────────────────────────────────────── */}
      <h3 style={{ marginTop: 24, marginBottom: 6 }}>{t("Карта инструмента", "Tool map")}</h3>
      <div className="muted" style={{ fontSize: 12, marginBottom: 8 }}>
        {t("Это не игра — это инструмент. Шесть рабочих поверхностей. Числа живые, из БД.",
           "This is not a game, it is a tool. Six working surfaces. Counts are live, from the DB.")}
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: 12,
        }}
      >
        <MapCell
          title={t("Корпус", "Corpus")}
          count={counts.corpus}
          unit={t("записей", "entries")}
          to="/library"
          body={
            counts.corpusByKind ? (
              <>
                {countLine(counts.corpusByKind, "attractor",     t("аттракторов", "attractors"))}
                {countLine(counts.corpusByKind, "r_root",        t("R-корней", "R-roots"))}
                {countLine(counts.corpusByKind, "breed",         t("пород", "breeds"))}
                {countLine(counts.corpusByKind, "chimera",       t("химер", "chimeras"))}
                {countLine(counts.corpusByKind, "source_card",   t("сырых карточек", "raw cards"))}
                {countLine(counts.corpusByKind, "micro_aspect",  t("аспектов пород", "breed aspects"))}
                {countLine(counts.corpusByKind, "phase_doc",     t("документов фаз разработки", "phase docs"))}
              </>
            ) : null
          }
          cta={t("Читать · искать · вызывать органы над записью",
                 "Read · search · summon organs on an entry")}
        />

        <MapCell
          title={t("Банки органов", "Organ banks")}
          count={counts.organs}
          unit={t("органов", "organs")}
          to="/configurator"
          body={
            <div className="muted" style={{ fontSize: 12 }}>
              {counts.organBanks ? `${counts.organBanks} ` : "8 "}
              {t("банков: поле, объект, действие, LLM-роль, кризис, след, мутация, деградация. Растут от триажа и химер.",
                 "banks: field, object, action, llm_role, crisis, trace, mutation, degradation. Grow from triage and chimeras.")}
            </div>
          }
          cta={t("Открыть конфигуратор", "Open configurator")}
        />

        <MapCell
          title={t("Конфигуратор + GameWeaver", "Configurator + GameWeaver")}
          count={null}
          unit=""
          to="/configurator"
          body={
            <div className="muted" style={{ fontSize: 12 }}>
              {t("Имя, функция, playable verb, стадия зрелости + чипы из банков. GameWeaver атакует черновик. Промотируешь → играешь.",
                 "Name, function, playable verb, maturity stage + organ chips. GameWeaver attacks the draft. Promote → play.")}
            </div>
          }
          cta={t("Собрать игру", "Assemble a game")}
        />

        <MapCell
          title={t("Триаж сырого материала", "Raw material triage")}
          count={counts.fates}
          unit={t("судеб", "fates")}
          to="/triage"
          body={
            <div className="muted" style={{ fontSize: 12 }}>
              {t("Похоронить · извлечь орган · оставить семенем · сжать до упражнения · поднять до игры · скрестить · вырастить породу · отложить · запретить. «Извлечь орган» наращивает банк.",
                 "Bury · extract organ · keep as seed · shrink to exercise · lift to game-exercise · cross · breed · defer to interface · forbid. 'Extract organ' grows the bank.")}
            </div>
          }
          cta={t("Открыть очередь", "Open the queue")}
        />

        <MapCell
          title={t("Гипотезы исследователя", "Researcher hypotheses")}
          count={null}
          unit=""
          to="/research"
          body={
            <div className="muted" style={{ fontSize: 12 }}>
              {t("Записать утверждение, атаковать его 4 органами, привязать к черновику игры, превратить в playable форму. Один клик = один ход роли, не чат.",
                 "Record a claim, attack it with 4 organs, link it to a game draft, turn it into a playable form. One click = one organ pass, not a chat.")}
            </div>
          }
          cta={t("Открыть верстак", "Open the workbench")}
        />

        <MapCell
          title={t("Профиль и playtest", "Profile and playtest")}
          count={gamesCount}
          unit={t("жанров", "genres")}
          to="/operator"
          body={
            <div className="muted" style={{ fontSize: 12 }}>
              {t("Качественный профиль по сессиям — слепоты, склонности, названные связки между жанрами. Playtest harness фиксирует рефлексии и 24h follow-up для переноса операции.",
                 "Qualitative profile from sessions — blindnesses, tendencies, named cross-genre connections. Playtest harness records reflections and a 24h follow-up for operation transfer.")}
            </div>
          }
          cta={t("Operator Profile · Playtest", "Operator Profile · Playtest")}
        />
      </div>

      {/* ── Правила сборки: честный код-пойнтер ─────────────────────────── */}
      <div className="card" style={{ marginTop: 12, fontSize: 12 }}>
        <b>{t("Правила сборки и онтология", "Assembly rules and ontology")}</b>
        {t(
          " — стадии зрелости (0–5), словарь судеб триажа, маппинг каноническая роль → runtime-роль, словарь cross-patterns профиля, дефолты банков — сейчас определяются в коде: ",
          " — maturity stages (0–5), triage fate vocabulary, canonical-role → runtime-role mapping, profile cross-pattern vocabulary, bank defaults — are currently defined in code: ",
        )}
        <code>backend/app/services/organ_seed.py</code>,{" "}
        <code>backend/app/services/genome_promote.py</code>,{" "}
        <code>backend/app/services/operator_profile.py</code>,{" "}
        <code>backend/app/api/triage.py</code>.{" "}
        {t("UI для их редактирования — отдельный заход. Сейчас правки только через PR.",
           "A UI for editing them is a separate pass. For now, changes go only through PRs.")}
      </div>

      {/* ── Список 12 жанров ────────────────────────────────────────────── */}
      <h3 style={{ marginTop: 24, marginBottom: 6 }}>
        {t("Игры", "Games")} <span className="muted" style={{ fontSize: 13, fontWeight: "normal" }}>
          · {gamesCount ?? "…"} {t("канонических жанров", "canonical genres")}
        </span>
      </h3>
      <div className="muted" style={{ fontSize: 12, marginBottom: 8 }}>
        {t(
          "Реальный материал берётся по умолчанию. LLM-модель — gpt-4.1-mini для большинства, grok-4-0709 для register_sapper и assistant_as_foreign.",
          "Real material is selected by default. LLM model — gpt-4.1-mini for most, grok-4-0709 for register_sapper and assistant_as_foreign.",
        )}
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
        {t(
          "Под капотом: FastAPI + SQLite + Vite/React. LLM через 302.ai. 12 жанров, 130 канонических органов, 4720 записей корпуса, 40 химерных ячеек. RC-0 заморозка нарушена два раза: для researcher workbench и для playtest harness. Подробнее — в ",
          "Under the hood: FastAPI + SQLite + Vite/React. LLM via 302.ai. 12 genres, 130 canonical organs, 4720 corpus entries, 40 chimera cells. The RC-0 freeze was broken twice: for the researcher workbench and the playtest harness. More in ",
        )}
        <code>docs/releases/MINDFIELD_RC0_FREEZE_2026-06-13.md</code>.
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

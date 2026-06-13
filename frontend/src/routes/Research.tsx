import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useT } from "../i18n";

export default function Research() {
  const t = useT();
  const [hyps, setHyps] = useState<any[] | null>(null);

  useEffect(() => {
    api.researchListHypotheses(true).then(setHyps).catch(() => setHyps([]));
  }, []);

  return (
    <div className="app">
      <div className="header">
        <Link to="/">← {t("все игры", "all games")}</Link>
        <span className="muted">Researcher Workbench</span>
      </div>

      <h2>Researcher Workbench</h2>
      <p style={{ fontSize: 14, lineHeight: 1.6 }}>
        {t(
          "Это инструмент для исследования психотехнических LLM-игр. Игроки тренируют операции различения; LLM работает не как помощник, а как игровой орган (прокурор / шпаклёвщик / адвокат ростка / литералист-чужой). У нас 12 канонических жанров, 130 канонических органов в 8 банках, 4720 записей корпуса и движок сборки новых игр.",
          "This is a research tool for psychotechnical LLM games. Players train operations of discrimination; the LLM acts not as an assistant but as a game-organ (prosecutor / spackler / sprout advocate / literal alien). We ship 12 canonical genres, 130 canonical organs in 8 banks, 4720 corpus entries, and an engine for assembling new games.",
        )}
      </p>

      <div className="card" style={{ marginTop: 12 }}>
        <h3 style={{ marginTop: 0 }}>{t("Что ты можешь делать как исследователь", "What you can do as a researcher")}</h3>
        <ol style={{ lineHeight: 1.7 }}>
          <li>
            <b><Link to="/library">{t("Читать корпус", "Read the corpus")}</Link></b>
            {t(
              " — 24 аттрактора, 12 R-корней, 12 пород, 40 химер, 4200 сырых карточек. FTS5-поиск. На любой записи — кнопки «атаковать прокурором», «заштукатурить», «защитить как росток», «прочитать буквально». Это не чат — один клик = один ход роли.",
              " — 24 attractors, 12 R-roots, 12 breeds, 40 chimeras, 4200 raw cards. FTS5 search. On any entry — buttons to attack with prosecutor / spackle / defend as sprout / read literally. This is not a chat — one click = one organ pass.",
            )}
          </li>
          <li>
            <b><Link to="/triage">{t("Триаж 4200", "Triage 4200")}</Link></b>
            {t(
              " — 9 судеб (похоронить / извлечь орган / оставить семенем / сжать до упражнения / поднять до игры / скрестить / вырастить породу / отложить до интерфейса / запретить). «Извлечь орган» наращивает банки конфигуратора.",
              " — 9 fates (bury / extract organ / keep as seed / shrink to exercise / lift to game / cross / breed / defer to interface / forbid). 'Extract organ' grows the configurator banks.",
            )}
          </li>
          <li>
            <b><Link to="/configurator">{t("Конфигуратор", "Configurator")}</Link></b>
            {t(
              " — сборщик черновика игры из 8 банков органов. Имя / функция / playable verb / стадия зрелости. Прогон через GameWeaver (playability_critic), который атакует черновик. Промотировав черновик с выбором field_type — играешь в собственную игру.",
              " — assemble a game draft from 8 organ banks. Name / function / playable verb / maturity stage. Run GameWeaver (playability_critic), which attacks the draft. Promote the draft with a field_type — and play your own game.",
            )}
          </li>
          <li>
            <b>{t("Гипотезы", "Hypotheses")}</b>
            {t(
              " (ниже) — запиши своё утверждение об операции, паттерне, породе. Вызови над ним один из 4 органов — получишь зафиксированное давление, не чат. Привяжи гипотезу к черновику конфигуратора, чтобы превратить её в играбельную форму.",
              " (below) — record your claim about an operation, a pattern, a breed. Summon one of the 4 organs over it — you get recorded pressure, not a chat. Link a hypothesis to a configurator draft to turn it into a playable form.",
            )}
          </li>
          <li>
            <b><Link to="/operator">Operator Profile</Link></b>
            {t(
              " — сквозной портрет игрока после нескольких сессий, с именованными связками между жанрами.",
              " — a cross-session portrait of the player after several sessions, with named connections between genres.",
            )}
          </li>
        </ol>
      </div>

      <div className="card" style={{ marginTop: 12 }}>
        <h3 style={{ marginTop: 0 }}>{t("Чего тут НЕТ", "What is NOT here")}</h3>
        <ul style={{ lineHeight: 1.6, fontSize: 13 }}>
          <li>{t("Никакого чата с ассистентом. LLM-роли всегда в форме одного хода организма.", "No chat with an assistant. LLM roles always come as a single organ pass.")}</li>
          <li>{t("Никаких числовых рейтингов игрока. Профиль качественный, не баллы.", "No numeric player ratings. The profile is qualitative, not points.")}</li>
          <li>{t("Никакой педагогики «правильного ответа». Игра ставит сцену, на которой видна твоя слепота.", "No pedagogy of 'correct answer'. The game stages a scene where your blindness becomes visible.")}</li>
          <li>{t("Никакого RAG / chat-агента / multiplayer. Это инструмент полевого различения, не платформа.", "No RAG / chat agent / multiplayer. This is a field-discrimination tool, not a platform.")}</li>
        </ul>
      </div>

      <div style={{ marginTop: 24, display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <h3 style={{ margin: 0 }}>{t("Мои гипотезы", "My hypotheses")}</h3>
        <Link to="/research/hypotheses/new" className="kbd" style={{ textDecoration: "none" }}>+ {t("новая гипотеза", "new hypothesis")}</Link>
      </div>

      {hyps && hyps.length === 0 && (
        <div className="muted" style={{ marginTop: 12, fontSize: 13 }}>
          {t("Гипотез ещё нет. Создай первую — что ты хочешь проверить?", "No hypotheses yet. Create the first one — what do you want to test?")}
        </div>
      )}
      {hyps?.map(h => (
        <Link key={h.id} to={`/research/hypotheses/${h.id}`} style={{ display: "block", textDecoration: "none", color: "inherit" }}>
          <div className="card" style={{ marginTop: 8 }}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <div>
                <b>{h.title}</b>{" "}
                <span className="kbd">{h.status}</span>
                {h.linked_draft_id && <span className="kbd" style={{ marginLeft: 4 }}>↪ draft</span>}
              </div>
              <span className="muted" style={{ fontSize: 11 }}>{h.updated_at?.slice(0,19)}</span>
            </div>
            {h.body_md && (
              <div className="muted" style={{ fontSize: 12, marginTop: 4 }}>
                {h.body_md.slice(0, 160)}{h.body_md.length > 160 && "…"}
              </div>
            )}
          </div>
        </Link>
      ))}
    </div>
  );
}

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

export default function Research() {
  const [hyps, setHyps] = useState<any[] | null>(null);

  useEffect(() => {
    api.researchListHypotheses(true).then(setHyps).catch(() => setHyps([]));
  }, []);

  return (
    <div className="app">
      <div className="header">
        <Link to="/">← все игры</Link>
        <span className="muted">Researcher Workbench</span>
      </div>

      <h2>Researcher Workbench</h2>
      <p style={{ fontSize: 14, lineHeight: 1.6 }}>
        Это инструмент для исследования <b>психотехнических LLM-игр</b>. Игроки тренируют операции
        различения; LLM работает не как помощник, а как игровой орган (прокурор / шпаклёвщик /
        адвокат ростка / литералист-чужой). У нас 12 канонических жанров, 130 канонических органов
        в 8 банках, 4720 записей корпуса и движок сборки новых игр.
      </p>

      <div className="card" style={{ marginTop: 12 }}>
        <h3 style={{ marginTop: 0 }}>Что ты можешь делать как исследователь</h3>
        <ol style={{ lineHeight: 1.7 }}>
          <li>
            <b><Link to="/library">Читать корпус</Link></b> — 24 аттрактора, 12 R-корней, 12 пород,
            40 химер, 4200 сырых карточек. FTS5-поиск. На любой записи — кнопки «атаковать прокурором»,
            «заштукатурить», «защитить как росток», «прочитать буквально». Это не чат — один клик = один ход роли.
          </li>
          <li>
            <b><Link to="/triage">Триаж 4200</Link></b> — 9 судеб (похоронить / извлечь орган / оставить
            семенем / сжать до упражнения / поднять до игры / скрестить / вырастить породу / отложить
            до интерфейса / запретить). «Извлечь орган» наращивает банки конфигуратора.
          </li>
          <li>
            <b><Link to="/configurator">Конфигуратор</Link></b> — сборщик черновика игры из 8 банков
            органов. Имя / функция / playable verb / стадия зрелости. Прогон через GameWeaver
            (playability_critic), который атакует черновик. Промотировав черновик с выбором field_type —
            играешь в собственную игру.
          </li>
          <li>
            <b>Гипотезы</b> (ниже) — запиши своё утверждение об операции, паттерне, породе.
            Вызови над ним один из 4 органов — получишь зафиксированное давление, не чат. Привяжи
            гипотезу к черновику конфигуратора, чтобы превратить её в играбельную форму.
          </li>
          <li>
            <b><Link to="/operator">Operator Profile</Link></b> — сквозной портрет игрока после
            нескольких сессий, с именованными связками между жанрами.
          </li>
        </ol>
      </div>

      <div className="card" style={{ marginTop: 12 }}>
        <h3 style={{ marginTop: 0 }}>Чего тут НЕТ</h3>
        <ul style={{ lineHeight: 1.6, fontSize: 13 }}>
          <li>Никакого чата с ассистентом. LLM-роли всегда в форме одного хода организма.</li>
          <li>Никаких числовых рейтингов игрока. Профиль качественный, не баллы.</li>
          <li>Никакой педагогики «правильного ответа». Игра ставит сцену, на которой видна твоя слепота.</li>
          <li>Никакого RAG / chat-агента / multiplayer. Это инструмент полевого различения, не платформа.</li>
        </ul>
      </div>

      <div style={{ marginTop: 24, display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <h3 style={{ margin: 0 }}>Мои гипотезы</h3>
        <Link to="/research/hypotheses/new" className="kbd" style={{ textDecoration: "none" }}>+ новая гипотеза</Link>
      </div>

      {hyps && hyps.length === 0 && (
        <div className="muted" style={{ marginTop: 12, fontSize: 13 }}>
          Гипотез ещё нет. Создай первую — что ты хочешь проверить?
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

import { useLang, setLang } from "../i18n";

/* Tiny RU/EN toggle. Reloads the page to flush all in-flight fetches and
 * any cached pre-translation rendering. Side-effect path is simpler than
 * threading the lang state through every route's data-fetch hook. */
export default function LanguageSwitcher() {
  const { lang } = useLang();
  return (
    <div style={{ display: "inline-flex", gap: 0, border: "1px solid var(--border)", borderRadius: 3, overflow: "hidden" }}>
      <button
        onClick={() => { if (lang !== "ru") { setLang("ru"); window.location.reload(); } }}
        style={{
          fontSize: 11, padding: "2px 8px", border: "none",
          background: lang === "ru" ? "rgba(80,160,80,0.25)" : "var(--bg)",
          color: lang === "ru" ? "var(--accent)" : "inherit",
          cursor: "pointer",
        }}
        title="русский"
      >
        RU
      </button>
      <button
        onClick={() => { if (lang !== "en") { setLang("en"); window.location.reload(); } }}
        style={{
          fontSize: 11, padding: "2px 8px", border: "none",
          background: lang === "en" ? "rgba(80,160,80,0.25)" : "var(--bg)",
          color: lang === "en" ? "var(--accent)" : "inherit",
          cursor: "pointer",
        }}
        title="English"
      >
        EN
      </button>
    </div>
  );
}

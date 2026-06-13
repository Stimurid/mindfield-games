/* Tiny i18n. No external dependency.
 *
 * - `lang` lives in localStorage.mindfield.lang ∈ {ru, en}.
 * - `useT()` returns a `t(ru, en?)` function that picks the right side.
 * - `lang` change re-renders subscribers via a CustomEvent.
 * - `getLang()` is also exported for the api client (which is not a component).
 */
import { createContext, useContext, useEffect, useState } from "react";

type Lang = "ru" | "en";
const KEY = "mindfield.lang";
const EVT = "mindfield-lang-changed";

export function getLang(): Lang {
  const v = (localStorage.getItem(KEY) as Lang | null) ?? "ru";
  return v === "en" ? "en" : "ru";
}

export function setLang(next: Lang) {
  localStorage.setItem(KEY, next);
  window.dispatchEvent(new CustomEvent(EVT, { detail: next }));
}

interface Ctx { lang: Lang; setLang: (l: Lang) => void; }
const LangCtx = createContext<Ctx>({ lang: "ru", setLang });

export function LangProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>(getLang());
  useEffect(() => {
    const handler = (e: Event) => {
      const next = (e as CustomEvent).detail as Lang;
      setLangState(next);
    };
    window.addEventListener(EVT, handler);
    return () => window.removeEventListener(EVT, handler);
  }, []);
  return (
    <LangCtx.Provider value={{ lang, setLang }}>
      {children}
    </LangCtx.Provider>
  );
}

export function useLang() {
  return useContext(LangCtx);
}

export function useT() {
  const { lang } = useContext(LangCtx);
  return (ru: string, en?: string) => (lang === "en" && en !== undefined ? en : ru);
}

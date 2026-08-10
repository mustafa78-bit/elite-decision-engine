import { useTranslation } from "react-i18next";

export default function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const isEn = i18n.language?.startsWith("en");

  return (
    <button
      type="button"
      onClick={() => i18n.changeLanguage(isEn ? "tr" : "en")}
      className="text-[10px] font-mono uppercase tracking-wider text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors px-2 py-1 rounded border border-[var(--border-subtle)] hover:border-[var(--border-default)]"
      title="Change site language / Site dilini değiştir"
    >
      {isEn ? "EN 🇺🇸" : "TR 🇹🇷"}
    </button>
  );
}

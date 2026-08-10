import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const STORAGE_KEY = "ui_language";

// Auto-discovers every locales/<lang>/<namespace>.json file -- adding a new
// page's translations only means dropping a new file here, never editing
// this config (avoids merge conflicts when many pages are translated in
// parallel).
const enModules = import.meta.glob("./locales/en/*.json", { eager: true }) as Record<string, { default: Record<string, unknown> }>;
const trModules = import.meta.glob("./locales/tr/*.json", { eager: true }) as Record<string, { default: Record<string, unknown> }>;

function buildResources(modules: Record<string, { default: Record<string, unknown> }>): Record<string, Record<string, unknown>> {
  const result: Record<string, Record<string, unknown>> = {};
  for (const path in modules) {
    const match = path.match(/([^/]+)\.json$/);
    if (!match) continue;
    result[match[1]] = modules[path].default;
  }
  return result;
}

const enResources = buildResources(enModules);
const trResources = buildResources(trModules);
const namespaces = Object.keys(enResources);

function detectInitialLanguage(): "en" | "tr" {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "en" || stored === "tr") return stored;
  return navigator.language?.toLowerCase().startsWith("tr") ? "tr" : "en";
}

i18n.use(initReactI18next).init({
  resources: {
    en: enResources,
    tr: trResources,
  },
  ns: namespaces,
  defaultNS: "common",
  lng: detectInitialLanguage(),
  fallbackLng: "en",
  interpolation: {
    escapeValue: false,
  },
});

i18n.on("languageChanged", (lng) => {
  localStorage.setItem(STORAGE_KEY, lng);
});

export default i18n;

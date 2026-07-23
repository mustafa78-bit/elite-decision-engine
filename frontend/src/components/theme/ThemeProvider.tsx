import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from "react";

export type ThemeType = "terminal-dark" | "midnight-pro" | "professional-light";
export type AccentType = "blue" | "violet" | "green" | "orange" | "red";
export type DensityType = "compact" | "comfortable" | "spacious";

interface ThemeState {
  mode: "dark";
  setMode: (mode: "dark") => void;
  contrast: "normal" | "high";
  setContrast: (contrast: "normal" | "high") => void;
  density: DensityType;
  setDensity: (density: DensityType) => void;
  fontSize: "small" | "medium" | "large";
  setFontSize: (size: "small" | "medium" | "large") => void;
  reducedMotion: boolean;

  // Appearance System State
  theme: ThemeType;
  setTheme: (theme: ThemeType) => void;
  accent: AccentType;
  setAccent: (accent: AccentType) => void;
  autoTheme: boolean;
  setAutoTheme: (auto: boolean) => void;
}

const ThemeContext = createContext<ThemeState | null>(null);

function getSystemReducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [contrast, setContrast] = useState<"normal" | "high">(() => {
    return (localStorage.getItem("elide-contrast") as "normal" | "high") || "normal";
  });
  const [density, setDensity] = useState<DensityType>(() => {
    return (localStorage.getItem("elide-density") as DensityType) || "compact";
  });
  const [fontSize, setFontSize] = useState<"small" | "medium" | "large">(() => {
    return (localStorage.getItem("elide-font-size") as "small" | "medium" | "large") || "small";
  });
  const [reducedMotion, setReducedMotion] = useState(getSystemReducedMotion);

  // Advanced Appearance Settings
  const [theme, setTheme] = useState<ThemeType>(() => {
    return (localStorage.getItem("elide-theme") as ThemeType) || "terminal-dark";
  });
  const [accent, setAccent] = useState<AccentType>(() => {
    return (localStorage.getItem("elide-accent") as AccentType) || "blue";
  });
  const [autoTheme, setAutoTheme] = useState<boolean>(() => {
    return localStorage.getItem("elide-auto-theme") === "true";
  });

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const handler = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  const applySettings = useCallback(() => {
    const root = document.documentElement;
    root.setAttribute("data-density", density);
    root.setAttribute("data-contrast", contrast);
    root.setAttribute("data-font-size", fontSize);

    // Auto theme calculation
    let activeTheme = theme;
    if (autoTheme) {
      const systemIsDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      activeTheme = systemIsDark ? "terminal-dark" : "professional-light";
    }

    root.setAttribute("data-theme", activeTheme);
    root.setAttribute("data-accent", accent);

    localStorage.setItem("elide-density", density);
    localStorage.setItem("elide-contrast", contrast);
    localStorage.setItem("elide-font-size", fontSize);
    localStorage.setItem("elide-theme", theme);
    localStorage.setItem("elide-accent", accent);
    localStorage.setItem("elide-auto-theme", String(autoTheme));
  }, [density, contrast, fontSize, theme, accent, autoTheme]);

  useEffect(() => {
    applySettings();
  }, [applySettings]);

  // Listener for prefers-color-scheme changes when auto-theme is on
  useEffect(() => {
    if (!autoTheme) return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => applySettings();
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, [autoTheme, applySettings]);

  const handleSetDensity = useCallback((d: DensityType) => {
    setDensity(d);
  }, []);

  const handleSetContrast = useCallback((c: "normal" | "high") => {
    setContrast(c);
  }, []);

  const handleSetFontSize = useCallback((s: "small" | "medium" | "large") => {
    setFontSize(s);
  }, []);

  return (
    <ThemeContext.Provider
      value={{
        mode: "dark",
        setMode: () => {},
        contrast,
        setContrast: handleSetContrast,
        density,
        setDensity: handleSetDensity,
        fontSize,
        setFontSize: handleSetFontSize,
        reducedMotion,
        theme,
        setTheme,
        accent,
        setAccent,
        autoTheme,
        setAutoTheme,
      }}
    >
      <style>{`
        [data-font-size="small"] { --text-scale: 0.875; }
        [data-font-size="medium"] { --text-scale: 1; }
        [data-font-size="large"] { --text-scale: 1.125; }
        [data-contrast="high"] {
          --text-primary: #FFFFFF;
          --text-secondary: #CBD5E1;
          --border-subtle: #475569;
        }
      `}</style>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeState {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}

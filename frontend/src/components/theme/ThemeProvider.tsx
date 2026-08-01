import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from "react";

type ThemeMode = "dark";

interface ThemeState {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  contrast: "normal" | "high";
  setContrast: (contrast: "normal" | "high") => void;
  density: "compact" | "comfortable" | "spacious";
  setDensity: (density: "compact" | "comfortable" | "spacious") => void;
  fontSize: "small" | "medium" | "large";
  setFontSize: (size: "small" | "medium" | "large") => void;
  reducedMotion: boolean;
}

const ThemeContext = createContext<ThemeState | null>(null);

function getSystemReducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode] = useState<ThemeMode>("dark");
  const [contrast, setContrast] = useState<"normal" | "high">(() => {
    return (localStorage.getItem("elide-contrast") as "normal" | "high") || "normal";
  });
  const [density, setDensity] = useState<"compact" | "comfortable" | "spacious">(() => {
    return (localStorage.getItem("elide-density") as "compact" | "comfortable" | "spacious") || "compact";
  });
  const [fontSize, setFontSize] = useState<"small" | "medium" | "large">(() => {
    return (localStorage.getItem("elide-font-size") as "small" | "medium" | "large") || "small";
  });
  const [reducedMotion, setReducedMotion] = useState(getSystemReducedMotion);

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
    root.setAttribute("data-theme", mode);
    root.setAttribute("data-font-size", fontSize);
    localStorage.setItem("elide-density", density);
    localStorage.setItem("elide-contrast", contrast);
    localStorage.setItem("elide-font-size", fontSize);
  }, [density, contrast, mode, fontSize]);

  useEffect(() => {
    applySettings();
  }, [applySettings]);

  const handleSetDensity = useCallback((d: "compact" | "comfortable" | "spacious") => {
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
        mode,
        setMode: () => {},
        contrast,
        setContrast: handleSetContrast,
        density,
        setDensity: handleSetDensity,
        fontSize,
        setFontSize: handleSetFontSize,
        reducedMotion,
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

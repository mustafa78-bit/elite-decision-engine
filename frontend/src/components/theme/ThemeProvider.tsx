import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from "react";

type ThemeMode = "dark";

interface ThemeState {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  contrast: "normal" | "high";
  setContrast: (contrast: "normal" | "high") => void;
  density: "compact" | "comfortable" | "spacious";
  setDensity: (density: "compact" | "comfortable" | "spacious") => void;
  reducedMotion: boolean;
}

const ThemeContext = createContext<ThemeState | null>(null);

function getSystemReducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode] = useState<ThemeMode>("dark");
  const [contrast, setContrast] = useState<"normal" | "high">("normal");
  const [density, setDensity] = useState<"compact" | "comfortable" | "spacious">("compact");
  const [reducedMotion, setReducedMotion] = useState(getSystemReducedMotion);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const handler = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  const applyDensity = useCallback(() => {
    const root = document.documentElement;
    root.setAttribute("data-density", density);
    root.setAttribute("data-contrast", contrast);
    root.setAttribute("data-theme", mode);
  }, [density, contrast, mode]);

  useEffect(() => {
    applyDensity();
  }, [applyDensity]);

  return (
    <ThemeContext.Provider
      value={{
        mode,
        setMode: () => {},
        contrast,
        setContrast,
        density,
        setDensity,
        reducedMotion,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeState {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}

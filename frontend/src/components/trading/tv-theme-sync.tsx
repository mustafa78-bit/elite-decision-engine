import { useEffect } from "react";
import { useTheme } from "../theme/ThemeProvider";

interface TVThemeSyncProps {
  chart?: {
    applyOptions: (opts: Record<string, unknown>) => void;
  } | null;
}

export function TVThemeSync({ chart }: TVThemeSyncProps) {
  const { mode, contrast } = useTheme();

  useEffect(() => {
    if (!chart) return;
    chart.applyOptions({
      layout: {
        background: { type: 0 as any, color: "transparent" },
        textColor: contrast === "high" ? "#ffffff" : "rgba(255,255,255,0.4)",
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.03)" },
        horzLines: { color: "rgba(255,255,255,0.03)" },
      },
      crosshair: {
        vertLine: { color: "rgba(255,255,255,0.1)", width: 1, style: 2 },
        horzLine: { color: "rgba(255,255,255,0.1)", width: 1, style: 2 },
      },
      rightPriceScale: {
        borderColor: "rgba(255,255,255,0.06)",
      },
      timeScale: {
        borderColor: "rgba(255,255,255,0.06)",
      },
    });
  }, [chart, mode, contrast]);

  return null;
}

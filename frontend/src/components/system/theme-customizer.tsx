import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { useTheme } from "../theme/ThemeProvider";

const ACCENT_MAP: Record<string, string> = {
  dark: "#3b82f6",
  midnight: "#818cf8",
  matrix: "#22c55e",
  onyx: "#a855f7",
};

export function ThemeCustomizer() {
  const { contrast, setContrast, density, setDensity, fontSize, setFontSize } = useTheme();
  const [selectedTheme, setSelectedTheme] = useState(() => localStorage.getItem("elide-theme-preset") || "dark");
  const [glowIntensity, setGlowIntensity] = useState(() => {
    const saved = localStorage.getItem("elide-glow-intensity");
    return saved ? Number(saved) : 60;
  });

  const themes = [
    { name: "Dark", id: "dark", accent: "#3b82f6" },
    { name: "Midnight", id: "midnight", accent: "#818cf8" },
    { name: "Matrix", id: "matrix", accent: "#22c55e" },
    { name: "Onyx", id: "onyx", accent: "#a855f7" },
  ];

  useEffect(() => {
    localStorage.setItem("elide-theme-preset", selectedTheme);
    const accent = ACCENT_MAP[selectedTheme] || "#3b82f6";
    document.documentElement.style.setProperty("--accent-blue", accent);
  }, [selectedTheme]);

  useEffect(() => {
    localStorage.setItem("elide-glow-intensity", String(glowIntensity));
    document.documentElement.style.setProperty("--glow-intensity", `${glowIntensity}%`);
  }, [glowIntensity]);

  return (
    <Card className="h-full">
      <CardHeader><CardTitle>Theme Customizer</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <div>
          <div className="text-[12px] font-mono text-[var(--text-muted)] mb-1 uppercase">Presets</div>
          <div className="flex gap-1.5">
            {themes.map((t) => (
              <button
                key={t.id}
                onClick={() => setSelectedTheme(t.id)}
                className={`flex-1 p-2 rounded-lg border transition-all ${
                  selectedTheme === t.id
                    ? "border-[var(--accent-blue)] bg-[var(--bg-hover)]"
                    : "border-[var(--border-subtle)] bg-[var(--bg-base)]"
                }`}
              >
                <div className="flex gap-0.5 mb-1">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: t.accent }} />
                  <div className="w-2 h-2 rounded-full bg-[var(--text-muted)]" />
                </div>
                <div className="text-[12px] font-mono text-center">{t.name}</div>
              </button>
            ))}
          </div>
        </div>
        <div>
          <div className="text-[12px] font-mono text-[var(--text-muted)] mb-1 uppercase">Density</div>
          <div className="flex gap-1">
            {(["compact", "comfortable", "spacious"] as const).map((d) => (
              <button
                key={d}
                onClick={() => setDensity(d)}
                className={`flex-1 py-1 rounded text-[12px] font-mono border capitalize ${
                  density === d
                    ? "bg-[var(--accent-blue)]/20 border-[var(--accent-blue)] text-[var(--accent-blue)]"
                    : "bg-[var(--bg-base)] border-[var(--border-subtle)] text-[var(--text-muted)]"
                }`}
              >
                {d}
              </button>
            ))}
          </div>
        </div>
        <div>
          <div className="text-[12px] font-mono text-[var(--text-muted)] mb-1 uppercase">Contrast</div>
          <div className="flex gap-1">
            {(["normal", "high"] as const).map((c) => (
              <button
                key={c}
                onClick={() => setContrast(c)}
                className={`flex-1 py-1 rounded text-[12px] font-mono border capitalize ${
                  contrast === c
                    ? "bg-[var(--accent-blue)]/20 border-[var(--accent-blue)] text-[var(--accent-blue)]"
                    : "bg-[var(--bg-base)] border-[var(--border-subtle)] text-[var(--text-muted)]"
                }`}
              >
                {c}
              </button>
            ))}
          </div>
        </div>
        <div>
          <div className="text-[12px] font-mono text-[var(--text-muted)] mb-1 uppercase">Font Size</div>
          <div className="flex gap-1">
            {(["small", "medium", "large"] as const).map((s) => (
              <button
                key={s}
                onClick={() => setFontSize(s)}
                className={`flex-1 py-1 rounded text-[12px] font-mono border capitalize ${
                  fontSize === s
                    ? "bg-[var(--accent-blue)]/20 border-[var(--accent-blue)] text-[var(--accent-blue)]"
                    : "bg-[var(--bg-base)] border-[var(--border-subtle)] text-[var(--text-muted)]"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
        <div>
          <div className="text-[12px] font-mono text-[var(--text-muted)] mb-1 uppercase">Glow Intensity</div>
          <div className="flex items-center gap-2">
            <input
              type="range"
              min="0"
              max="100"
              value={glowIntensity}
              onChange={(e) => setGlowIntensity(Number(e.target.value))}
              className="flex-1 h-1 accent-[var(--accent-blue)]"
            />
            <span className="text-[12px] font-mono w-8 text-right">{glowIntensity}%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

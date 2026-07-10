import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface ThemeOption {
  name: string;
  primary: string;
  bg: string;
  accent: string;
}

export function ThemeCustomizer() {
  const [selectedTheme, setSelectedTheme] = useState("dark");
  const [glowIntensity, setGlowIntensity] = useState(60);
  const [fontSize, setFontSize] = useState("small");

  const themes: ThemeOption[] = [
    { name: "Dark", primary: "#0a0e17", bg: "#111827", accent: "#3b82f6" },
    { name: "Midnight", primary: "#0a0a1a", bg: "#0f0f2e", accent: "#818cf8" },
    { name: "Matrix", primary: "#000a00", bg: "#001a00", accent: "#22c55e" },
    { name: "Onyx", primary: "#0d0d0d", bg: "#1a1a1a", accent: "#a855f7" },
  ];

  return (
    <Card className="h-full">
      <CardHeader><CardTitle>Theme Customizer</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <div>
          <div className="text-[9px] font-mono text-[var(--text-muted)] mb-1 uppercase">Presets</div>
          <div className="flex gap-1.5">
            {themes.map((t) => (
              <button
                key={t.name}
                onClick={() => setSelectedTheme(t.name.toLowerCase())}
                className={`flex-1 p-2 rounded-lg border transition-all ${
                  selectedTheme === t.name.toLowerCase()
                    ? "border-[var(--accent-blue)] bg-[var(--bg-hover)]"
                    : "border-[var(--border-subtle)] bg-[var(--bg-base)]"
                }`}
              >
                <div className="flex gap-0.5 mb-1">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: t.accent }} />
                  <div className="w-2 h-2 rounded-full bg-[var(--text-muted)]" />
                </div>
                <div className="text-[9px] font-mono text-center">{t.name}</div>
              </button>
            ))}
          </div>
        </div>
        <div>
          <div className="text-[9px] font-mono text-[var(--text-muted)] mb-1 uppercase">Glow Intensity</div>
          <div className="flex items-center gap-2">
            <input
              type="range"
              min="0"
              max="100"
              value={glowIntensity}
              onChange={(e) => setGlowIntensity(Number(e.target.value))}
              className="flex-1 h-1 accent-[var(--accent-blue)]"
            />
            <span className="text-[10px] font-mono w-8 text-right">{glowIntensity}%</span>
          </div>
        </div>
        <div>
          <div className="text-[9px] font-mono text-[var(--text-muted)] mb-1 uppercase">Font Size</div>
          <div className="flex gap-1">
            {["small", "medium", "large"].map((size) => (
              <button
                key={size}
                onClick={() => setFontSize(size)}
                className={`flex-1 py-1 rounded text-[9px] font-mono border capitalize ${
                  fontSize === size
                    ? "bg-[var(--accent-blue)]/20 border-[var(--accent-blue)] text-[var(--accent-blue)]"
                    : "bg-[var(--bg-base)] border-[var(--border-subtle)] text-[var(--text-muted)]"
                }`}
              >
                {size}
              </button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

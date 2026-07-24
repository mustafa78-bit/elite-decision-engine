import { useMemo } from "react";
import { useWorkspaceStore, type Panel } from "../../stores/workspace-store";

interface ValidationResult {
  valid: boolean;
  issues: string[];
  panelCount: number;
  overlappingPanels: number;
  offscreenPanels: number;
  minSizeViolations: number;
}

export function validateLayout(panels: Panel[], viewportW = 1920, viewportH = 1080): ValidationResult {
  const issues: string[] = [];
  let overlappingPanels = 0;
  let offscreenPanels = 0;
  let minSizeViolations = 0;

  if (panels.length === 0) {
    return { valid: true, issues: [], panelCount: 0, overlappingPanels: 0, offscreenPanels: 0, minSizeViolations: 0 };
  }

  for (let i = 0; i < panels.length; i++) {
    const a = panels[i];

    if (a.w < 100) { minSizeViolations++; issues.push(`${a.title}: width ${a.w}px < 100px minimum`); }
    if (a.h < 60) { minSizeViolations++; issues.push(`${a.title}: height ${a.h}px < 60px minimum`); }
    if (a.x + a.w > viewportW * 1.5) { offscreenPanels++; issues.push(`${a.title}: extends beyond viewport`); }
    if (a.y + a.h > viewportH * 1.5) { offscreenPanels++; issues.push(`${a.title}: below viewport`); }

    for (let j = i + 1; j < panels.length; j++) {
      const b = panels[j];
      const overlap = !(a.x + a.w <= b.x || b.x + b.w <= a.x || a.y + a.h <= b.y || b.y + b.h <= a.y);
      if (overlap) { overlappingPanels++; }
    }
  }

  return {
    valid: issues.length === 0,
    issues,
    panelCount: panels.length,
    overlappingPanels,
    offscreenPanels,
    minSizeViolations,
  };
}

export function LayoutValidator() {
  const { panels } = useWorkspaceStore();
  const result = useMemo(() => validateLayout(panels), [panels]);

  if (result.valid && result.panelCount <= 1) return null;

  return (
    <div className="px-2 py-1.5">
      <div className="text-[12px] font-mono text-[var(--text-muted)] uppercase tracking-wider mb-1">
        Layout
      </div>
      <div className="flex items-center gap-2 text-[12px] font-mono">
        <span className={result.valid ? "text-[var(--accent-green)]" : "text-[var(--accent-yellow)]"}>
          {result.panelCount} panels
        </span>
        {result.overlappingPanels > 0 && (
          <span className="text-[var(--accent-yellow)]">
            {result.overlappingPanels} overlaps
          </span>
        )}
        {result.offscreenPanels > 0 && (
          <span className="text-[var(--accent-red)]">
            {result.offscreenPanels} offscreen
          </span>
        )}
        {result.minSizeViolations > 0 && (
          <span className="text-[var(--accent-red)]">
            {result.minSizeViolations} undersized
          </span>
        )}
      </div>
    </div>
  );
}

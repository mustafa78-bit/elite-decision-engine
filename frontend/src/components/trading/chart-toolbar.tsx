import { cn } from "../../lib/utils";

interface ChartToolbarProps {
  onDraw?: () => void;
  onMarker?: () => void;
  onCrosshair?: () => void;
  onReset?: () => void;
  drawingMode?: boolean;
  crosshairMode?: boolean;
}

export function ChartToolbar({
  onDraw,
  onMarker,
  onCrosshair,
  onReset,
  drawingMode,
  crosshairMode,
}: ChartToolbarProps) {
  return (
    <div className="flex items-center gap-0.5 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] p-0.5">
      <ToolbarButton
        icon="✏"
        label="Draw"
        active={drawingMode}
        onClick={onDraw}
      />
      <ToolbarButton
        icon="📌"
        label="Marker"
        active={false}
        onClick={onMarker}
      />
      <ToolbarButton
        icon="⊹"
        label="Crosshair"
        active={crosshairMode}
        onClick={onCrosshair}
      />
      <div className="w-px h-3 bg-[var(--border-subtle)] mx-0.5" />
      <ToolbarButton
        icon="↺"
        label="Reset"
        active={false}
        onClick={onReset}
      />
    </div>
  );
}

function ToolbarButton({
  icon,
  label,
  active,
  onClick,
}: {
  icon: string;
  label: string;
  active?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "px-1.5 py-1 rounded-md text-[9px] font-mono transition-all flex items-center gap-1",
        active
          ? "bg-[var(--accent-blue)]/15 text-[var(--accent-blue)]"
          : "text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-base)]",
      )}
      title={label}
    >
      <span>{icon}</span>
      <span className="hidden md:inline">{label}</span>
    </button>
  );
}

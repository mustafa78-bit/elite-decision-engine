import { cn } from "../../lib/utils";
import { useWorkspaceStore } from "../../stores/workspace-store";
import { useUIStore } from "../../stores/ui-store";

export function FullscreenToggle() {
  const { fullscreen, toggleFullscreen } = useWorkspaceStore();
  return (
    <button
      onClick={toggleFullscreen}
      className={cn(
        "px-2 py-1 rounded-lg text-[10px] font-mono transition-all",
        fullscreen
          ? "bg-[var(--accent-blue)]/10 text-[var(--accent-blue)] border border-[var(--accent-blue)]/20"
          : "text-[var(--text-muted)] hover:text-[var(--text-secondary)] border border-transparent",
      )}
      title={fullscreen ? "Exit fullscreen" : "Fullscreen"}
    >
      {fullscreen ? "⛶ Exit" : "⛶ Fullscreen"}
    </button>
  );
}

export function FocusModeToggle() {
  const { setSidebarCollapsed, sidebarCollapsed } = useWorkspaceStore();
  const focus = sidebarCollapsed;
  return (
    <button
      onClick={() => setSidebarCollapsed(!focus)}
      className={cn(
        "px-2 py-1 rounded-lg text-[10px] font-mono transition-all",
        focus
          ? "bg-[var(--accent-blue)]/10 text-[var(--accent-blue)] border border-[var(--accent-blue)]/20"
          : "text-[var(--text-muted)] hover:text-[var(--text-secondary)] border border-transparent",
      )}
      title={focus ? "Exit focus mode" : "Focus mode"}
    >
      {focus ? "◎ Exit Focus" : "◎ Focus"}
    </button>
  );
}

export function CompactModeToggle() {
  const { setCommandPaletteOpen } = useUIStore();
  return (
    <button
      onClick={() => setCommandPaletteOpen(true)}
      className="px-2 py-1 rounded-lg text-[10px] font-mono text-[var(--text-muted)] hover:text-[var(--text-secondary)] border border-transparent hover:border-[var(--border-subtle)] transition-all"
      title="Command palette"
    >
      ⌘ Compact
    </button>
  );
}

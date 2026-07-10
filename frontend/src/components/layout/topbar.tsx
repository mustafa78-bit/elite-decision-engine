import { useUIStore } from "../../stores/ui-store";
import { useTerminalStore } from "../../stores/terminal-store";
import { useWorkspaceStore } from "../../stores/workspace-store";
import { Kbd } from "../ui/kbd";
import { FullscreenToggle, FocusModeToggle } from "../workspace/mode-toggles";
import { WorkspacePresets } from "../workspace/workspace-presets";
import { NotificationCenter } from "./notification-center";
import { ConnectionIndicator } from "./connection-indicator";

export default function Topbar() {
  const { setCommandPaletteOpen, setGlobalSearchOpen } = useUIStore();
  const { symbol, setSymbol, recentSymbols } = useTerminalStore();
  const { fullscreen } = useWorkspaceStore();

  if (fullscreen) {
    return (
      <header className="h-8 flex items-center justify-end px-3 bg-[var(--bg-base)] border-b border-[var(--border-subtle)]">
        <FullscreenToggle />
      </header>
    );
  }

  return (
    <header className="h-10 flex items-center justify-between px-4 border-b border-[var(--border-subtle)] bg-[var(--bg-base)] shrink-0">
      <div className="flex items-center gap-3">
        <button
          onClick={() => setCommandPaletteOpen(true)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:border-[var(--border-default)] transition-all"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          Search
          <Kbd>⌘K</Kbd>
        </button>

        <button
          onClick={() => setGlobalSearchOpen(true)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:border-[var(--border-default)] transition-all"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
          Navigate
          <Kbd>⌃K</Kbd>
        </button>

        <div className="flex items-center gap-2">
          {recentSymbols.slice(0, 4).map((s) => (
            <button
              key={s}
              onClick={() => setSymbol(s)}
              className={`px-2 py-0.5 rounded text-[10px] font-mono font-medium transition-all ${
                symbol === s
                   ? "text-[var(--accent-blue)] bg-[var(--accent-blue)]/10 border border-[var(--accent-blue)]/20"
                  : "text-[var(--text-muted)] hover:text-[var(--text-secondary)] border border-transparent"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <FocusModeToggle />
        <FullscreenToggle />
        <WorkspacePresets />
        <NotificationCenter />
        <ConnectionIndicator status="connected" />

        <span className="text-[10px] text-[var(--text-muted)] font-mono">
          {new Date().toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: false,
          })}
        </span>
        <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-green)] animate-pulse" />
      </div>
    </header>
  );
}

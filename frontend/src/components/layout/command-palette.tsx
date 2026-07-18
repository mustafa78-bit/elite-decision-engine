import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useUIStore } from "../../stores/ui-store";
import { useTerminalStore } from "../../stores/terminal-store";
import { useWorkspaceStore } from "../../stores/workspace-store";
import { useKeyboardShortcut, useFocusTrap } from "../../lib/accessibility";

interface Command {
  id: string;
  label: string;
  description: string;
  category: string;
  path?: string;
  action?: (() => void) | string;
  shortcut?: string;
}

const defaultCommands: Command[] = [
  { id: "dashboard", label: "Go to Dashboard", description: "View main dashboard", category: "Navigation", path: "/dashboard" },
  { id: "hero-dashboard", label: "Go to Hero Dashboard", description: "Enhanced dashboard view", category: "Navigation", path: "/hero-dashboard" },
  { id: "scanner", label: "Go to Scanner", description: "Market opportunity scanner", category: "Navigation", path: "/scanner" },
  { id: "portfolio", label: "Go to Portfolio", description: "View portfolio details", category: "Navigation", path: "/portfolio-detail" },
  { id: "trades", label: "Go to Trades", description: "View open and closed trades", category: "Navigation", path: "/trades" },
  { id: "analytics", label: "Go to Analytics", description: "Performance analytics", category: "Navigation", path: "/analytics" },
  { id: "market", label: "Go to Market", description: "Market overview", category: "Navigation", path: "/market" },
  { id: "signals", label: "Go to Signals", description: "Trading signals", category: "Navigation", path: "/signals" },
  { id: "decisions", label: "Go to Decision Center", description: "AI decision center", category: "Navigation", path: "/decisions" },
  { id: "risk", label: "Go to Risk", description: "Risk metrics", category: "Navigation", path: "/risk" },
  { id: "timeline", label: "Go to Timeline", description: "Event timeline", category: "Navigation", path: "/timeline" },
  { id: "watchlists", label: "Go to Watchlists", description: "Manage watchlists", category: "Navigation", path: "/watchlists" },
  { id: "execution", label: "Go to Execution", description: "Trading execution", category: "Navigation", path: "/execution" },
  { id: "intelligence", label: "Go to Intelligence", description: "Market intelligence", category: "Navigation", path: "/intelligence" },
  { id: "settings", label: "Go to Preferences", description: "User preferences", category: "Navigation", path: "/preferences" },
  { id: "toggle-sidebar", label: "Toggle Sidebar", description: "Show/hide navigation sidebar", category: "Actions", action: "toggle-sidebar", shortcut: "Ctrl+B" },
  { id: "focus-mode", label: "Toggle Focus Mode", description: "Minimize distractions", category: "Actions", action: "focus-mode" },
  { id: "toggle-fullscreen", label: "Toggle Fullscreen", description: "Enter/exit fullscreen", category: "Actions", action: "fullscreen" },
  { id: "refresh", label: "Refresh Data", description: "Reload all dashboard data", category: "Actions", shortcut: "Ctrl+R" },
  { id: "new-trade", label: "New Trade", description: "Open new trade form", category: "Actions", shortcut: "Ctrl+T" },
];

export function CommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen, setGlobalSearchOpen } = useUIStore();
  const { addCommand } = useTerminalStore();
  const { toggleSidebar, toggleFocusMode, toggleFullscreen } = useWorkspaceStore();
  const [query, setQuery] = useState("");
  const [focusedIdx, setFocusedIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const focusTrapRef = useFocusTrap(commandPaletteOpen);

  useKeyboardShortcut("k", () => {
    setGlobalSearchOpen(false);
    setCommandPaletteOpen(!commandPaletteOpen);
  }, { ctrl: true });

  useKeyboardShortcut("Escape", () => {
    if (commandPaletteOpen) setCommandPaletteOpen(false);
  });

  useEffect(() => {
    if (commandPaletteOpen) {
      setQuery("");
      setFocusedIdx(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [commandPaletteOpen]);

  if (!commandPaletteOpen) return null;

  const categories = Array.from(new Set(defaultCommands.map((c) => c.category)));

  const flatCommands = defaultCommands;
  const filtered = query
    ? flatCommands.filter(
        (c) =>
          c.label.toLowerCase().includes(query.toLowerCase()) ||
          c.description.toLowerCase().includes(query.toLowerCase()),
      )
    : flatCommands;

  const grouped = query
    ? [{ category: "Results", commands: filtered }]
    : categories.map((cat) => ({
        category: cat,
        commands: flatCommands.filter((c) => c.category === cat),
      }));

  const handleAction = useCallback((cmd: Command) => {
    if (cmd.action === "toggle-sidebar") { toggleSidebar(); return; }
    if (cmd.action === "focus-mode") { toggleFocusMode(); return; }
    if (cmd.action === "fullscreen") { toggleFullscreen(); return; }
    if (cmd.action === "refresh") { window.location.reload(); return; }
    if (cmd.action === "new-trade") { navigate("/trades"); return; }
  }, [toggleSidebar, toggleFocusMode, toggleFullscreen, navigate]);

  const handleSelect = (cmd: Command) => {
    addCommand(cmd.label);
    setCommandPaletteOpen(false);
    if (cmd.action) {
      handleAction(cmd);
    } else if (cmd.path) {
      navigate(cmd.path);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setFocusedIdx((i) => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setFocusedIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && filtered[focusedIdx]) {
      handleSelect(filtered[focusedIdx]);
    }
  };

  return (
    <div
      ref={focusTrapRef}
      className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] bg-black/40 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) setCommandPaletteOpen(false);
      }}
    >
      <div className="rounded-2xl shadow-2xl w-full max-w-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] animate-fadeSlideUp">
        <div className="flex items-center gap-3 px-4 py-3 border-b border-[var(--border-subtle)]">
          <svg className="w-4 h-4 text-[var(--text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setFocusedIdx(0);
            }}
            onKeyDown={handleKeyDown}
            placeholder="Search commands..."
            className="flex-1 bg-transparent text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none"
          />
          <span className="text-[10px] text-[var(--text-muted)] font-mono border border-[var(--border-subtle)] rounded px-1.5 py-0.5">
            ESC
          </span>
        </div>
        <div className="max-h-72 overflow-y-auto p-2">
          {grouped.map((group) => (
            <div key={group.category}>
              <div className="px-2 py-1.5 text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
                {group.category}
              </div>
              {group.commands.map((cmd) => {
                const flatIdx = filtered.indexOf(cmd);
                return (
                  <button
                    key={cmd.id}
                    onClick={() => handleSelect(cmd)}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors text-left group ${
                      focusedIdx === flatIdx
                        ? "bg-[var(--accent-blue)]/10 text-[var(--accent-blue)]"
                        : "hover:bg-[var(--bg-hover)]"
                    }`}
                  >
                    <div>
                      <div className={`text-sm ${focusedIdx === flatIdx ? "text-[var(--accent-blue)]" : "text-[var(--text-primary)]"}`}>
                        {cmd.label}
                      </div>
                      <div className="text-[11px] text-[var(--text-muted)]">{cmd.description}</div>
                    </div>
                    {cmd.shortcut && (
                      <span className="text-[9px] text-[var(--text-muted)] font-mono border border-[var(--border-subtle)] rounded px-1.5 py-0.5">
                        {cmd.shortcut}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          ))}
          {filtered.length === 0 && (
            <div className="px-3 py-8 text-center text-sm text-[var(--text-muted)]">
              No commands found
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

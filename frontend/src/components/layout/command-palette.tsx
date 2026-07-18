import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useUIStore } from "../../stores/ui-store";
import { useTerminalStore } from "../../stores/terminal-store";

interface Command {
  id: string;
  label: string;
  description: string;
  path?: string;
  action?: () => void;
  shortcut?: string;
}

const defaultCommands: Command[] = [
  { id: "dashboard", label: "Go to Dashboard", description: "View main dashboard", path: "/dashboard" },
  { id: "portfolio", label: "Go to Portfolio", description: "View portfolio details", path: "/portfolio-detail" },
  { id: "trades", label: "Go to Trades", description: "View open and closed trades", path: "/trades" },
  { id: "timeline", label: "Go to Timeline", description: "View event timeline", path: "/timeline" },
  { id: "watchlists", label: "Go to Watchlists", description: "Manage watchlists", path: "/watchlists" },
  { id: "analytics", label: "Go to Analytics", description: "View performance analytics", path: "/analytics" },
  { id: "settings", label: "Go to Preferences", description: "User preferences", path: "/preferences" },
];

export function CommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen } = useUIStore();
  const { addCommand } = useTerminalStore();
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCommandPaletteOpen(!commandPaletteOpen);
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [commandPaletteOpen, setCommandPaletteOpen]);

  useEffect(() => {
    let timer: any;
    if (commandPaletteOpen) {
      setQuery("");
      timer = setTimeout(() => inputRef.current?.focus(), 50);
    }
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [commandPaletteOpen]);

  if (!commandPaletteOpen) return null;

  const filtered = query
    ? defaultCommands.filter(
        (c) =>
          c.label.toLowerCase().includes(query.toLowerCase()) ||
          c.description.toLowerCase().includes(query.toLowerCase()),
      )
    : defaultCommands;

  const handleSelect = (cmd: Command) => {
    addCommand(cmd.label);
    setCommandPaletteOpen(false);
    if (cmd.path) navigate(cmd.path);
    cmd.action?.();
  };

  return (
    <div
      className="fixed inset-0 z-[var(--z-command)] flex items-start justify-center pt-[15vh]"
      onClick={(e) => {
        if (e.target === e.currentTarget) setCommandPaletteOpen(false);
      }}
    >
      <div className="glass-strong rounded-2xl shadow-[var(--shadow-lg)] w-full max-w-lg animate-slide-down">
        <div className="flex items-center gap-3 px-4 py-3 border-b border-[var(--glass-border)]">
          <svg className="w-4 h-4 text-[var(--text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search commands..."
            className="flex-1 bg-transparent text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none"
          />
          <span className="text-[10px] text-[var(--text-muted)] font-mono border border-[var(--border-subtle)] rounded px-1.5 py-0.5">
            ESC
          </span>
        </div>
        <div className="max-h-64 overflow-y-auto p-2">
          {filtered.map((cmd) => (
            <button
              key={cmd.id}
              onClick={() => handleSelect(cmd)}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-[var(--bg-hover)] transition-colors text-left group"
            >
              <div>
                <div className="text-sm text-[var(--text-primary)]">{cmd.label}</div>
                <div className="text-[11px] text-[var(--text-muted)]">{cmd.description}</div>
              </div>
              {cmd.shortcut && (
                <span className="text-[10px] text-[var(--text-muted)] font-mono border border-[var(--border-subtle)] rounded px-1.5 py-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                  {cmd.shortcut}
                </span>
              )}
            </button>
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

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useUIStore } from "../../stores/ui-store";
import { useTerminalStore } from "../../stores/terminal-store";
import { useWorkspaceStore } from "../../stores/workspace-store";
import { useKeyboardShortcut } from "../../lib/accessibility";

interface SearchItem {
  label: string;
  path: string;
  icon: string;
  action?: string;
}

const searchCategories: { name: string; items: SearchItem[] }[] = [
  {
    name: "Pages",
    items: [
      { label: "Dashboard", path: "/dashboard", icon: "◈" },
      { label: "Trades", path: "/trades", icon: "⇄" },
      { label: "Analytics", path: "/analytics", icon: "▦" },
      { label: "Market", path: "/market", icon: "◉" },
      { label: "Signals", path: "/signals", icon: "⚡" },
      { label: "Risk", path: "/risk", icon: "▲" },
      { label: "Portfolio Detail", path: "/portfolio-detail", icon: "▣" },
      { label: "Intelligence", path: "/intelligence", icon: "✦" },
      { label: "Execution", path: "/execution", icon: "▶" },
      { label: "Watchlists", path: "/watchlists", icon: "☰" },
      { label: "Funding", path: "/funding", icon: "◎" },
      { label: "Open Interest", path: "/open-interest", icon: "◐" },
      { label: "Whale Activity", path: "/whale", icon: "◉" },
      { label: "Liquidity", path: "/liquidity", icon: "≈" },
      { label: "Timeline", path: "/timeline", icon: "≡" },
      { label: "Paper Trading", path: "/paper-trading", icon: "◻" },
      { label: "Preferences", path: "/preferences", icon: "⚙" },
      { label: "Backtest", path: "/backtest", icon: "◈" },
    ],
  },
  {
    name: "Actions",
    items: [
      { label: "Search Symbols", path: "", icon: "🔍", action: "symbol-search" },
      { label: "Toggle Sidebar", path: "", icon: "◰", action: "toggle-sidebar" },
      { label: "Toggle Fullscreen", path: "", icon: "⛶", action: "toggle-fullscreen" },
      { label: "Focus Mode", path: "", icon: "◎", action: "focus-mode" },
    ],
  },
  {
    name: "Symbols",
    items: [
      { label: "Bitcoin", path: "", icon: "₿", action: "symbol-BTC/USDT" },
      { label: "Ethereum", path: "", icon: "⟠", action: "symbol-ETH/USDT" },
      { label: "Solana", path: "", icon: "◎", action: "symbol-SOL/USDT" },
    ],
  },
];

export function GlobalSearch() {
  const { globalSearchOpen, setGlobalSearchOpen } = useUIStore();
  const { setSymbol } = useTerminalStore();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [focusedIdx, setFocusedIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const { toggleSidebar: wsToggleSidebar, toggleFullscreen: wsToggleFullscreen } = useWorkspaceStore();

  useKeyboardShortcut("k", () => setGlobalSearchOpen(true), { ctrl: true });
  useKeyboardShortcut("Escape", () => { if (globalSearchOpen) setGlobalSearchOpen(false); });

  useEffect(() => {
    if (globalSearchOpen) {
      setQuery("");
      setFocusedIdx(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [globalSearchOpen]);

  const flatItems: SearchItem[] = searchCategories.flatMap((cat) => cat.items);
  const filtered = query
    ? flatItems.filter((item) =>
        item.label.toLowerCase().includes(query.toLowerCase()),
      )
    : flatItems;

  const handleSelect = useCallback(
    (item: (typeof flatItems)[0]) => {
      setGlobalSearchOpen(false);
      if (item.action?.startsWith("symbol-")) {
        setSymbol(item.action.replace("symbol-", ""));
      } else if (item.action === "symbol-search") {
        setGlobalSearchOpen(false);
      } else if (item.action === "toggle-sidebar") {
        wsToggleSidebar();
      } else if (item.action === "toggle-fullscreen") {
        wsToggleFullscreen();
      } else if (item.path) {
        navigate(item.path);
      }
    },
    [navigate, setGlobalSearchOpen, setSymbol, wsToggleSidebar, wsToggleFullscreen],
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setFocusedIdx((i) => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setFocusedIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && filtered[focusedIdx]) {
      handleSelect(filtered[focusedIdx]);
    } else if (e.key === "Escape") {
      setGlobalSearchOpen(false);
    }
  };

  return (
    <AnimatePresence>
      {globalSearchOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] bg-black/60 backdrop-blur-sm"
          onClick={() => setGlobalSearchOpen(false)}
        >
          <motion.div
            initial={{ opacity: 0, y: -20, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.96 }}
            transition={{ duration: 0.15 }}
            className="w-[560px] rounded-2xl border border-[var(--border-default)] bg-[var(--bg-elevated)] backdrop-blur-2xl shadow-2xl shadow-black/40 overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-3 border-b border-[var(--border-subtle)]">
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setFocusedIdx(0);
                }}
                onKeyDown={handleKeyDown}
                placeholder="Search pages, symbols, actions..."
                className="w-full bg-[var(--bg-base)] rounded-xl px-4 py-2.5 text-sm font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] border border-[var(--border-subtle)] focus:outline-none focus:border-[var(--accent-blue)]"
              />
            </div>
            <div className="max-h-80 overflow-y-auto p-2">
              {!query &&
                searchCategories.map((cat) => (
                  <div key={cat.name}>
                    <div className="px-2 py-1.5 text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
                      {cat.name}
                    </div>
                    {cat.items.map((item) => {
                      const flatIdx = flatItems.indexOf(item);
                      return (
                        <button
                          key={item.label}
                          onClick={() => handleSelect(item)}
                          className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs transition-all ${
                            focusedIdx === flatIdx
                              ? "bg-[var(--accent-blue)]/10 text-[var(--accent-blue)]"
                              : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-base)]"
                          }`}
                        >
                          <span className="w-5 text-center text-sm">{item.icon}</span>
                          <span className="font-mono">{item.label}</span>
                        </button>
                      );
                    })}
                  </div>
                ))}
              {query &&
                filtered.map((item, i) => (
                  <button
                    key={item.label}
                    onClick={() => handleSelect(item)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-xs transition-all ${
                      focusedIdx === i
                        ? "bg-[var(--accent-blue)]/10 text-[var(--accent-blue)]"
                        : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-base)]"
                    }`}
                  >
                    <span className="w-5 text-center text-sm">{item.icon}</span>
                    <span className="font-mono">{item.label}</span>
                  </button>
                ))}
              {query && filtered.length === 0 && (
                <div className="px-3 py-8 text-center text-xs text-[var(--text-muted)]">
                  No results for "{query}"
                </div>
              )}
            </div>
            <div className="px-3 py-2 border-t border-[var(--border-subtle)] flex gap-3">
              <span className="text-[9px] text-[var(--text-muted)] font-mono">
                ↑↓ Navigate
              </span>
              <span className="text-[9px] text-[var(--text-muted)] font-mono">
                ↵ Open
              </span>
              <span className="text-[9px] text-[var(--text-muted)] font-mono">
                Esc Close
              </span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

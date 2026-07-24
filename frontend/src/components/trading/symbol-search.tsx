import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../../lib/utils";
import { useTerminalStore } from "../../stores/terminal-store";

const popularSymbols = [
  { symbol: "BTC/USDT", name: "Bitcoin" },
  { symbol: "ETH/USDT", name: "Ethereum" },
  { symbol: "SOL/USDT", name: "Solana" },
  { symbol: "AVAX/USDT", name: "Avalanche" },
  { symbol: "LINK/USDT", name: "Chainlink" },
  { symbol: "DOT/USDT", name: "Polkadot" },
  { symbol: "MATIC/USDT", name: "Polygon" },
  { symbol: "UNI/USDT", name: "Uniswap" },
  { symbol: "ATOM/USDT", name: "Cosmos" },
  { symbol: "AAVE/USDT", name: "Aave" },
];

export function SymbolSearch() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [focusedIdx, setFocusedIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const ref = useRef<HTMLDivElement>(null);
  const { symbol, setSymbol, recentSymbols } = useTerminalStore();

  const filtered = query
    ? popularSymbols.filter(
        (s) =>
          s.symbol.toLowerCase().includes(query.toLowerCase()) ||
          s.name.toLowerCase().includes(query.toLowerCase()),
      )
    : popularSymbols;

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  const handleSelect = (sym: string) => {
    setSymbol(sym);
    setOpen(false);
    setQuery("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setFocusedIdx((i) => Math.min(i + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setFocusedIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && filtered[focusedIdx]) {
      handleSelect(filtered[focusedIdx].symbol);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  const displaySymbols = [
    ...(recentSymbols.length > 0
      ? recentSymbols.slice(0, 3).map((s) => ({ symbol: s, name: s }))
      : []),
    ...(recentSymbols.length > 0 ? [{ symbol: "---", name: "recent-divider" }] : []),
    ...filtered,
  ];

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-default)] text-xs font-mono text-[var(--text-primary)] hover:border-[var(--accent-blue)] transition-all"
      >
        <svg className="w-3.5 h-3.5 text-[var(--text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <span>{symbol}</span>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -4, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.96 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full left-0 mt-1 w-64 z-50 rounded-xl border border-[var(--border-default)] bg-[var(--bg-elevated)] backdrop-blur-xl shadow-2xl shadow-black/30 overflow-hidden"
          >
            <div className="p-2 border-b border-[var(--border-subtle)]">
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setFocusedIdx(0);
                }}
                onKeyDown={handleKeyDown}
                placeholder="Search symbols..."
                className="w-full bg-[var(--bg-base)] rounded-lg px-3 py-1.5 text-xs font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] border border-[var(--border-subtle)] focus:outline-none focus:border-[var(--accent-blue)]"
              />
            </div>
            <div className="max-h-64 overflow-y-auto p-1">
              {displaySymbols.map((item, i) => {
                if (item.name === "recent-divider") {
                  return (
                    <div key="divider" className="px-2 py-1 text-[12px] text-[var(--text-muted)] uppercase tracking-wider">
                      Recent
                    </div>
                  );
                }
                return (
                  <button
                    key={item.symbol}
                    onClick={() => handleSelect(item.symbol)}
                    className={cn(
                      "w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-xs transition-all",
                      focusedIdx === i
                        ? "bg-[var(--accent-blue)]/10 text-[var(--accent-blue)]"
                        : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-base)]",
                    )}
                  >
                    <span className="font-mono">{item.symbol}</span>
                    <span className="text-[12px] text-[var(--text-muted)]">{item.name}</span>
                  </button>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Badge } from "../ui/badge";
import { cn } from "../../lib/utils";

interface Notification {
  id: string;
  title: string;
  message: string;
  type: "info" | "success" | "warning" | "error";
  time: string;
  read: boolean;
  category: string;
}

const sampleNotifications: Notification[] = [
  { id: "1", title: "Signal Generated", message: "BTC/USDT buy signal detected with 82% confidence", type: "success", time: "2m ago", read: false, category: "signals" },
  { id: "2", title: "Risk Alert", message: "Portfolio VaR exceeded 2% threshold", type: "warning", time: "15m ago", read: false, category: "risk" },
  { id: "3", title: "Execution Report", message: "Limit order filled: 0.5 BTC @ $42,100", type: "info", time: "1h ago", read: true, category: "execution" },
  { id: "4", title: "System Health", message: "All systems operational", type: "success", time: "2h ago", read: true, category: "system" },
  { id: "5", title: "Connection Lost", message: "WebSocket reconnected after 3s downtime", type: "error", time: "3h ago", read: true, category: "system" },
];

const typeStyles: Record<string, string> = {
  info: "bg-[var(--accent-blue)]/10 border-[var(--accent-blue)]/20",
  success: "bg-[var(--accent-green)]/10 border-[var(--accent-green)]/20",
  warning: "bg-[var(--accent-yellow)]/10 border-[var(--accent-yellow)]/20",
  error: "bg-[var(--accent-red)]/10 border-[var(--accent-red)]/20",
};

const typeDots: Record<string, string> = {
  info: "var(--accent-blue)",
  success: "var(--accent-green)",
  warning: "var(--accent-yellow)",
  error: "var(--accent-red)",
};

export function NotificationCenter() {
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState<string>("all");
  const [notifications, setNotifications] = useState(sampleNotifications);

  const categories = ["all", "signals", "risk", "execution", "system"];
  const unread = notifications.filter((n) => !n.read).length;

  const filtered = filter === "all"
    ? notifications
    : notifications.filter((n) => n.category === filter);

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="relative px-2 py-1 rounded-lg text-[10px] font-mono text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] transition-all"
      >
        🔔 Notifications
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-[var(--accent-red)] text-white text-[7px] font-mono flex items-center justify-center">
            {unread}
          </span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -4, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -4, scale: 0.96 }}
            className="absolute top-full right-0 mt-1 w-80 z-50 rounded-xl border border-[var(--border-default)] bg-[var(--bg-elevated)] backdrop-blur-2xl shadow-2xl overflow-hidden"
          >
            <div className="p-3 border-b border-[var(--border-subtle)]">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-[var(--text-primary)]">
                    Notifications
                  </span>
                  {unread > 0 && (
                    <Badge variant="danger">{unread} new</Badge>
                  )}
                </div>
                {unread > 0 && (
                  <button
                    onClick={markAllRead}
                    className="text-[9px] font-mono text-[var(--accent-blue)] hover:underline"
                  >
                    Mark all read
                  </button>
                )}
              </div>
              <div className="flex gap-1">
                {categories.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setFilter(cat)}
                    className={cn(
                      "px-1.5 py-0.5 rounded text-[8px] font-mono uppercase tracking-wider transition-all",
                      filter === cat
                        ? "bg-[var(--accent-blue)]/10 text-[var(--accent-blue)]"
                        : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]",
                    )}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>
            <div className="max-h-72 overflow-y-auto">
              {filtered.map((n) => (
                <div
                  key={n.id}
                  className={cn(
                    "px-3 py-2 border-b border-[var(--border-subtle)] last:border-b-0 transition-colors",
                    !n.read ? "bg-[var(--accent-blue)]/5" : "",
                  )}
                >
                  <div className="flex items-start gap-2">
                    <span
                      className="w-2 h-2 rounded-full mt-1 shrink-0"
                      style={{ backgroundColor: typeDots[n.type] }}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-mono font-medium text-[var(--text-primary)]">
                          {n.title}
                        </span>
                        <span className="text-[8px] font-mono text-[var(--text-muted)]">
                          {n.time}
                        </span>
                      </div>
                      <p className="text-[9px] text-[var(--text-secondary)] mt-0.5">
                        {n.message}
                      </p>
                      <div className="flex gap-1 mt-1">
                        <span className={cn("text-[8px] font-mono uppercase tracking-wider px-1 rounded", typeStyles[n.type])}>
                          {n.type}
                        </span>
                        <span className="text-[8px] font-mono text-[var(--text-muted)]">
                          {n.category}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              {filtered.length === 0 && (
                <div className="px-3 py-8 text-center text-[10px] text-[var(--text-muted)]">
                  No {filter} notifications
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

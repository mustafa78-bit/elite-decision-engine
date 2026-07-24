import type { NotificationRow } from "../../api/notifications";

interface Props {
  notification: NotificationRow;
  onMarkRead: (id: number) => void;
}

const EVENT_LABELS: Record<string, string> = {
  TRADE_OPENED: "Trade Opened",
  TRADE_CLOSED: "Trade Closed",
  MARKET_UPDATE: "Market Update",
  SIGNAL_UPDATE: "Signal Update",
  RISK_UPDATE: "Risk Update",
};

const EVENT_COLORS: Record<string, string> = {
  TRADE_OPENED: "text-green-400",
  TRADE_CLOSED: "text-red-400",
  MARKET_UPDATE: "text-blue-400",
  SIGNAL_UPDATE: "text-purple-400",
  RISK_UPDATE: "text-yellow-400",
};

function formatTime(iso: string | null): string {
  if (!iso) return "\u2014";
  const d = new Date(iso);
  return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function previewPayload(payload: Record<string, unknown>): string {
  const entries = Object.entries(payload).slice(0, 3);
  return entries.map(([k, v]) => `${k}=${v}`).join(" ");
}

export default function NotificationItem({ notification, onMarkRead }: Props) {
  const label = EVENT_LABELS[notification.event_type] || notification.event_type;
  const color = EVENT_COLORS[notification.event_type] || "text-[var(--text-secondary)]";

  return (
    <div
      className={`flex items-start gap-3 px-3 py-2 border-b border-gray-800 last:border-0 transition-colors ${
        notification.read ? "opacity-50" : "bg-gray-900/50"
      }`}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={`text-[12px] font-semibold uppercase tracking-wider ${color}`}>
            {label}
          </span>
          {!notification.read && (
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0" />
          )}
        </div>
        <p className="text-[13px] text-[var(--text-secondary)] truncate mt-0.5">
          {previewPayload(notification.payload)}
        </p>
        <p className="text-[12px] text-[var(--text-muted)] mt-0.5">{formatTime(notification.created_at)}</p>
      </div>
      {!notification.read && (
        <button
          onClick={() => onMarkRead(notification.id)}
          className="text-[12px] text-[var(--text-muted)] hover:text-[var(--text-secondary)] uppercase tracking-wider shrink-0 mt-1"
        >
          Read
        </button>
      )}
    </div>
  );
}

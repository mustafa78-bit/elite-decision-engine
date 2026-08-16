import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
import type { NotificationRow } from "../../api/notifications";

interface Props {
  notification: NotificationRow;
  onMarkRead: (id: number) => void;
}

const EVENT_LABEL_KEYS: Record<string, string> = {
  TRADE_OPENED: "item.eventLabels.tradeOpened",
  TRADE_CLOSED: "item.eventLabels.tradeClosed",
  SYSTEM_HEALTH_DEGRADED: "item.eventLabels.systemHealthDegraded",
  SYSTEM_HEALTH_RECOVERED: "item.eventLabels.systemHealthRecovered",
};

const EVENT_COLORS: Record<string, string> = {
  TRADE_OPENED: "text-green-400",
  TRADE_CLOSED: "text-red-400",
  SYSTEM_HEALTH_DEGRADED: "text-yellow-400",
  SYSTEM_HEALTH_RECOVERED: "text-blue-400",
};

function formatTime(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function formatPnl(pnl: unknown): string {
  const n = typeof pnl === "number" ? pnl : Number(pnl);
  if (Number.isNaN(n)) return "N/A";
  return `${n > 0 ? "+" : ""}${n.toFixed(2)}`;
}

function formatMessage(t: TFunction, notification: NotificationRow): string {
  const p = notification.payload;
  switch (notification.event_type) {
    case "TRADE_OPENED":
      return t("item.messages.tradeOpened", {
        symbol: p.symbol ?? "?",
        side: p.side ?? "?",
        entry: p.entry ?? "?",
      });
    case "TRADE_CLOSED":
      return t("item.messages.tradeClosed", {
        symbol: p.symbol ?? "?",
        side: p.side ?? "?",
        pnl: formatPnl(p.pnl),
        reason: p.close_reason ?? p.status ?? "?",
      });
    case "SYSTEM_HEALTH_DEGRADED":
      return t("item.messages.systemHealthDegraded", {
        component: p.component ?? "?",
        detail: p.detail ? ` — ${p.detail}` : "",
      });
    case "SYSTEM_HEALTH_RECOVERED":
      return t("item.messages.systemHealthRecovered", {
        component: p.component ?? "?",
      });
    default:
      return t("item.messages.unknown", { eventType: notification.event_type });
  }
}

export default function NotificationItem({ notification, onMarkRead }: Props) {
  const { t } = useTranslation("notifications");
  const labelKey = EVENT_LABEL_KEYS[notification.event_type];
  const label = labelKey ? t(labelKey) : notification.event_type;
  const color = EVENT_COLORS[notification.event_type] || "text-gray-400";

  return (
    <div
      className={`flex items-start gap-3 px-3 py-2 border-b border-gray-800 last:border-0 transition-colors ${
        notification.read ? "opacity-50" : "bg-gray-900/50"
      }`}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={`text-[10px] font-semibold uppercase tracking-wider ${color}`}>
            {label}
          </span>
          {!notification.read && (
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0" />
          )}
        </div>
        <p className="text-[11px] text-gray-400 truncate mt-0.5">
          {formatMessage(t, notification)}
        </p>
        <p className="text-[9px] text-gray-600 mt-0.5">{formatTime(notification.created_at)}</p>
      </div>
      {!notification.read && (
        <button
          onClick={() => onMarkRead(notification.id)}
          className="text-[9px] text-gray-600 hover:text-gray-300 uppercase tracking-wider shrink-0 mt-1"
        >
          {t("item.markRead")}
        </button>
      )}
    </div>
  );
}

import type { ConnectionStatus } from "../types/connection";
import type { WsEvent } from "../types/trade";

export type { ConnectionStatus };

export type MessageHandler = (data: WsEvent) => void;
export type StatusHandler = (status: ConnectionStatus) => void;

const WS_BASE = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000";

function getToken(): string {
  return localStorage.getItem("auth_token") ?? "";
}

function createSocket(
  path: string,
  onMessage: MessageHandler,
  onStatus?: StatusHandler,
): WebSocket {
  const token = getToken();
  const url = `${WS_BASE}${path}?token=${encodeURIComponent(token)}`;
  const ws = new WebSocket(url);

  ws.onopen = () => onStatus?.("CONNECTED");
  ws.onmessage = (event: MessageEvent) => {
    try {
      const data: WsEvent = JSON.parse(event.data);
      onMessage(data);
    } catch {
      console.warn("Failed to parse WebSocket message", event.data);
    }
  };
  ws.onclose = () => onStatus?.("DISCONNECTED");
  ws.onerror = () => onStatus?.("DISCONNECTED");

  return ws;
}

export function connectTradesSocket(
  onMessage: MessageHandler,
  onStatus?: StatusHandler,
): WebSocket {
  return createSocket("/ws/trades", onMessage, onStatus);
}

export function connectAnalyticsSocket(
  onMessage: MessageHandler,
  onStatus?: StatusHandler,
): WebSocket {
  return createSocket("/ws/analytics", onMessage, onStatus);
}

export function connectPortfolioSocket(
  onMessage: MessageHandler,
  onStatus?: StatusHandler,
): WebSocket {
  return createSocket("/ws/portfolio", onMessage, onStatus);
}

export function connectNotificationsSocket(
  onMessage: MessageHandler,
  onStatus?: StatusHandler,
): WebSocket {
  return createSocket("/ws/notifications", onMessage, onStatus);
}

export function connectPreferencesSocket(
  onMessage: MessageHandler,
  onStatus?: StatusHandler,
): WebSocket {
  return createSocket("/ws/preferences", onMessage, onStatus);
}

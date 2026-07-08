import type { TradeNotification } from "../types/trade.ts";

export type ConnectionStatus = "CONNECTED" | "DISCONNECTED";

type MessageHandler = (data: TradeNotification) => void;
type StatusHandler = (status: ConnectionStatus) => void;

export function connectTradesSocket(
  onMessage: MessageHandler,
  onStatus?: StatusHandler,
): WebSocket {
  const ws = new WebSocket("ws://localhost:8000/ws/trades");

  ws.onopen = () => {
    onStatus?.("CONNECTED");
  };

  ws.onmessage = (event: MessageEvent) => {
    try {
      const data: TradeNotification = JSON.parse(event.data);
      onMessage(data);
    } catch {
      console.warn("Failed to parse WebSocket message", event.data);
    }
  };

  ws.onclose = () => {
    onStatus?.("DISCONNECTED");
  };

  ws.onerror = () => {
    onStatus?.("DISCONNECTED");
  };

  return ws;
}

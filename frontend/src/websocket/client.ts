import type { TradeNotification } from "../types/trade.ts";

type MessageHandler = (data: TradeNotification) => void;

export function connectTradesSocket(
  onMessage: MessageHandler,
): WebSocket {
  const ws = new WebSocket("ws://localhost:8000/ws/trades");

  ws.onmessage = (event: MessageEvent) => {
    try {
      const data: TradeNotification = JSON.parse(event.data);
      onMessage(data);
    } catch {
      console.warn("Failed to parse WebSocket message", event.data);
    }
  };

  ws.onclose = () => {
    console.log("WebSocket disconnected");
  };

  ws.onerror = (err) => {
    console.error("WebSocket error", err);
  };

  return ws;
}

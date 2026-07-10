import { useEffect, useRef, useState, useCallback } from "react";
import type { ConnectionStatus } from "../types/connection";
import type { WsEvent } from "../types/trade";

interface UseWebSocketOptions {
  url: string;
  onMessage?: (data: WsEvent) => void;
  onStatus?: (status: ConnectionStatus) => void;
  reconnectInterval?: number;
  maxRetries?: number;
}

interface UseWebSocketReturn {
  status: ConnectionStatus;
  retryCount: number;
  send: (data: string) => void;
  reconnect: () => void;
}

export function useWebSocket({
  url,
  onMessage,
  onStatus,
  reconnectInterval = 3000,
  maxRetries = 10,
}: UseWebSocketOptions): UseWebSocketReturn {
  const [status, setStatus] = useState<ConnectionStatus>("DISCONNECTED");
  const [retryCount, setRetryCount] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout>>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus("CONNECTED");
        setRetryCount(0);
        onStatus?.("CONNECTED");
      };

      ws.onmessage = (event: MessageEvent) => {
        try {
          const data: WsEvent = JSON.parse(event.data);
          onMessage?.(data);
        } catch {
          console.warn("Failed to parse WebSocket message", event.data);
        }
      };

      ws.onclose = () => {
        setStatus("DISCONNECTED");
        onStatus?.("DISCONNECTED");
        wsRef.current = null;
        attemptReconnect();
      };

      ws.onerror = () => {
        setStatus("DISCONNECTED");
        onStatus?.("DISCONNECTED");
        ws.close();
      };
    } catch {
      attemptReconnect();
    }
  }, [url, onMessage, onStatus]);

  const attemptReconnect = useCallback(() => {
    if (retryCount >= maxRetries) return;
    setRetryCount((prev) => prev + 1);
    retryTimerRef.current = setTimeout(connect, reconnectInterval);
  }, [retryCount, maxRetries, reconnectInterval, connect]);

  const send = useCallback((data: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(data);
    }
  }, []);

  const reconnect = useCallback(() => {
    setRetryCount(0);
    wsRef.current?.close();
    connect();
  }, [connect]);

  useEffect(() => {
    connect();
    return () => {
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { status, retryCount, send, reconnect };
}

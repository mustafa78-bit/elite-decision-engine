import { useCallback, useEffect, useRef, useState } from "react";

export type ConnectionStatus = "CONNECTED" | "DISCONNECTED" | "RECONNECTING";

export interface WsEvent<T = unknown> {
  event: string;
  timestamp: string;
  payload: T;
}

export type MessageHandler = (data: WsEvent) => void;

interface UseWebSocketOptions {
  onMessage?: MessageHandler;
  reconnectInterval?: number;
  maxRetries?: number;
}

export function useWebSocket(url: string, options: UseWebSocketOptions = {}) {
  const { onMessage, reconnectInterval = 3000, maxRetries = 10 } = options;
  const [status, setStatus] = useState<ConnectionStatus>("DISCONNECTED");
  const wsRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("CONNECTED");
      retryCountRef.current = 0;
    };

    ws.onmessage = (event: MessageEvent) => {
      try {
        const data: WsEvent = JSON.parse(event.data);
        onMessage?.(data);
      } catch {
        console.warn("Failed to parse WS message", event.data);
      }
    };

    ws.onclose = () => {
      setStatus("DISCONNECTED");
      wsRef.current = null;
      if (retryCountRef.current < maxRetries) {
        setStatus("RECONNECTING");
        timerRef.current = setTimeout(() => {
          retryCountRef.current++;
          connect();
        }, reconnectInterval);
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [url, onMessage, reconnectInterval, maxRetries]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(timerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  return { status, send };
}

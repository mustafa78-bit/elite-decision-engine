import { useCallback, useEffect, useRef, useState } from "react";
import { addGlobalToast } from "../components/layout/ToastProvider";

interface LiveUpdateConfig<T> {
  url: string;
  initialData?: T;
  onMessage?: (data: T) => void;
  reconnectInterval?: number;
  maxRetries?: number;
}

export function useLiveUpdates<T = unknown>(config: LiveUpdateConfig<T>) {
  const { url, initialData, onMessage, reconnectInterval = 3000, maxRetries = 10 } = config;
  const [data, setData] = useState<T | undefined>(initialData);
  const [connected, setConnected] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      retryRef.current = 0;
    };

    ws.onmessage = (event: MessageEvent) => {
      try {
        const parsed = JSON.parse(event.data) as T;
        setData(parsed);
        onMessage?.(parsed);
      } catch {
        console.warn("Failed to parse live update", event.data);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;
      if (retryRef.current < maxRetries) {
        timerRef.current = setTimeout(() => {
          retryRef.current++;
          connect();
        }, reconnectInterval);
      }
    };

    ws.onerror = () => ws.close();
  }, [url, onMessage, reconnectInterval, maxRetries]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(timerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { data, connected };
}

export function useNotificationUpdates() {
  const prevNotifRef = useRef(0);

  const onMessage = useCallback((_data: unknown) => {
    prevNotifRef.current++;
    addGlobalToast(`New notification received`, "info");
  }, []);

  return useLiveUpdates({
    url: "ws://localhost:8000/ws/notifications",
    onMessage,
    reconnectInterval: 5000,
  });
}

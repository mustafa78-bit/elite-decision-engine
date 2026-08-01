import { useCallback, useState } from "react";

export interface Toast {
  id: string;
  message: string;
  type: "success" | "error" | "info" | "warning";
  duration?: number;
}

let toastId = 0;

const listeners: Array<(toasts: Toast[]) => void> = [];
let toasts: Toast[] = [];

function notify() {
  listeners.forEach((l) => l([...toasts]));
}

export function addToast(message: string, type: Toast["type"] = "info", duration = 4000) {
  const id = String(++toastId);
  toasts = [...toasts, { id, message, type, duration }];
  notify();
  if (duration > 0) {
    setTimeout(() => dismissToast(id), duration);
  }
  return id;
}

export function dismissToast(id: string) {
  toasts = toasts.filter((t) => t.id !== id);
  notify();
}

export function useToast() {
  const [state, setState] = useState<Toast[]>(toasts);

  useCallback(() => {
    const handler = (next: Toast[]) => setState(next);
    listeners.push(handler);
    setState([...toasts]);
    return () => {
      const idx = listeners.indexOf(handler);
      if (idx >= 0) listeners.splice(idx, 1);
    };
  }, []);

  return {
    toasts: state,
    addToast,
    dismissToast,
  };
}

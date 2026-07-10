import { useSyncExternalStore } from "react";
import type { Toast } from "../../hooks/useToast";
import { dismissToast } from "../../hooks/useToast";

const listeners: Array<() => void> = [];
let toasts: Toast[] = [];

function subscribe(cb: () => void) {
  listeners.push(cb);
  return () => {
    const idx = listeners.indexOf(cb);
    if (idx >= 0) listeners.splice(idx, 1);
  };
}

function getSnapshot() {
  return toasts;
}

export function addGlobalToast(message: string, type: Toast["type"] = "info", duration = 4000) {
  const id = crypto.randomUUID();
  toasts = [...toasts, { id, message, type, duration }];
  listeners.forEach((l) => l());
  if (duration > 0) {
    setTimeout(() => {
      toasts = toasts.filter((t) => t.id !== id);
      listeners.forEach((l) => l());
    }, duration);
  }
  return id;
}

const typeStyles: Record<string, string> = {
  success: "border-green-800 bg-green-950 text-green-400",
  error: "border-red-800 bg-red-950 text-red-400",
  info: "border-blue-800 bg-blue-950 text-blue-400",
  warning: "border-yellow-800 bg-yellow-950 text-yellow-400",
};

export function ToastProvider() {
  const items = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);

  if (items.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {items.map((t) => (
        <div
          key={t.id}
          className={`border rounded px-4 py-2 text-xs font-mono flex items-center justify-between gap-3 animate-in slide-in-from-right ${typeStyles[t.type]}`}
        >
          <span>{t.message}</span>
          <button
            onClick={() => {
              toasts = toasts.filter((x) => x.id !== t.id);
              dismissToast(t.id);
            }}
            className="opacity-60 hover:opacity-100 transition-opacity"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}

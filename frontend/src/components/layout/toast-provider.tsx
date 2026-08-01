import { useUIStore, type Toast } from "../../stores/ui-store";

const typeStyles: Record<string, string> = {
  success:
    "border-[var(--accent-green)]/30 bg-[var(--accent-green)]/10 text-[var(--accent-green)]",
  error:
    "border-[var(--accent-red)]/30 bg-[var(--accent-red)]/10 text-[var(--accent-red)]",
  info: "border-[var(--accent-blue)]/30 bg-[var(--accent-blue)]/10 text-[var(--accent-blue)]",
  warning:
    "border-[var(--accent-yellow)]/30 bg-[var(--accent-yellow)]/10 text-[var(--accent-yellow)]",
};

export function addGlobalToast(message: string, type: Toast["type"] = "info", duration = 4000) {
  useUIStore.getState().addToast({ message, type, duration });
}

export function ToastProvider() {
  const { toasts, dismissToast } = useUIStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[var(--z-toast)] flex flex-col gap-2 max-w-sm">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`flex items-center justify-between gap-3 px-4 py-3 rounded-xl border shadow-lg animate-slide-up ${typeStyles[t.type]}`}
        >
          <span className="text-sm font-medium">{t.message}</span>
          <button
            onClick={() => dismissToast(t.id)}
            className="opacity-50 hover:opacity-100 transition-opacity text-sm"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}

import { create } from "zustand";

interface UIState {
  commandPaletteOpen: boolean;
  globalSearchOpen: boolean;
  activeModal: string | null;
  toasts: Toast[];
  setCommandPaletteOpen: (v: boolean) => void;
  setGlobalSearchOpen: (v: boolean) => void;
  setActiveModal: (id: string | null) => void;
  addToast: (toast: Omit<Toast, "id">) => void;
  dismissToast: (id: string) => void;
}

export interface Toast {
  id: string;
  message: string;
  type: "success" | "error" | "info" | "warning";
  duration?: number;
}

let toastCounter = 0;

export const useUIStore = create<UIState>((set) => ({
  commandPaletteOpen: false,
  globalSearchOpen: false,
  activeModal: null,
  toasts: [],

  setCommandPaletteOpen: (v) => set({ commandPaletteOpen: v }),
  setGlobalSearchOpen: (v) => set({ globalSearchOpen: v }),
  setActiveModal: (id) => set({ activeModal: id }),

  addToast: (toast) => {
    const id = String(++toastCounter);
    set((s) => ({ toasts: [...s.toasts, { ...toast, id }] }));
    const duration = toast.duration ?? 4000;
    if (duration > 0) {
      setTimeout(() => {
        set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
      }, duration);
    }
  },

  dismissToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

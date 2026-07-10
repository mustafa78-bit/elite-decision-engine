import { create } from "zustand";
import { persist } from "zustand/middleware";

interface PreferencesState {
  theme: "dark";
  sidebarCollapsed: boolean;
  refreshInterval: number;
  defaultSymbol: string;
  timeFormat: "12h" | "24h";
  numberFormat: "usd" | "compact";
  setTheme: (theme: "dark") => void;
  toggleSidebar: () => void;
  setRefreshInterval: (interval: number) => void;
  setDefaultSymbol: (symbol: string) => void;
  setTimeFormat: (format: "12h" | "24h") => void;
  setNumberFormat: (format: "usd" | "compact") => void;
}

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      theme: "dark",
      sidebarCollapsed: false,
      refreshInterval: 10_000,
      defaultSymbol: "BTC/USDT",
      timeFormat: "24h",
      numberFormat: "compact",
      setTheme: (theme) => set({ theme }),
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      setRefreshInterval: (refreshInterval) => set({ refreshInterval }),
      setDefaultSymbol: (defaultSymbol) => set({ defaultSymbol }),
      setTimeFormat: (timeFormat) => set({ timeFormat }),
      setNumberFormat: (numberFormat) => set({ numberFormat }),
    }),
    { name: "elite-preferences" },
  ),
);

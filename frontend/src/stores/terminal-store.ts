import { create } from "zustand";

interface TerminalState {
  symbol: string | null;
  recentSymbols: string[];
  favoriteSymbols: string[];
  pinnedWidgets: string[];
  commandHistory: string[];
  setSymbol: (s: string | null) => void;
  addRecentSymbol: (s: string) => void;
  toggleFavoriteSymbol: (s: string) => void;
  togglePinnedWidget: (id: string) => void;
  addCommand: (cmd: string) => void;
}

export const useTerminalStore = create<TerminalState>((set) => ({
  symbol: null,
  recentSymbols: ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
  favoriteSymbols: ["BTCUSDT"],
  pinnedWidgets: ["kpi", "portfolio"],
  commandHistory: [],

  setSymbol: (s) => set({ symbol: s }),

  addRecentSymbol: (s) =>
    set((state) => ({
      recentSymbols: [s, ...state.recentSymbols.filter((x) => x !== s)].slice(
        0,
        10,
      ),
    })),

  toggleFavoriteSymbol: (s) =>
    set((state) => ({
      favoriteSymbols: state.favoriteSymbols.includes(s)
        ? state.favoriteSymbols.filter((x) => x !== s)
        : [...state.favoriteSymbols, s],
    })),

  togglePinnedWidget: (id) =>
    set((state) => ({
      pinnedWidgets: state.pinnedWidgets.includes(id)
        ? state.pinnedWidgets.filter((x) => x !== id)
        : [...state.pinnedWidgets, id],
    })),

  addCommand: (cmd) =>
    set((state) => ({
      commandHistory: [cmd, ...state.commandHistory].slice(0, 50),
    })),
}));

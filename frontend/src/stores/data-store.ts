import { create } from "zustand";

interface KPI {
  name: string;
  value: number;
  unit: string;
  status: string;
  trend: string;
  change_pct?: number;
}

interface PortfolioSummary {
  total_pnl: number;
  win_rate: number;
  open_trades: number;
  profit_factor: number;
}

interface WatchlistItem {
  id: number;
  name: string;
  symbols: string[];
}

interface NotificationItem {
  id: string;
  event_type: string;
  created_at: string;
  read: boolean;
  metadata?: Record<string, unknown>;
}

interface DataState {
  kpis: KPI[];
  portfolio: PortfolioSummary | null;
  watchlists: WatchlistItem[];
  notifications: NotificationItem[];
  unreadNotifications: number;
  setKpis: (kpis: KPI[]) => void;
  setPortfolio: (portfolio: PortfolioSummary) => void;
  setWatchlists: (watchlists: WatchlistItem[]) => void;
  setNotifications: (notifications: NotificationItem[], unread: number) => void;
  markNotificationRead: (id: string) => void;
}

export const useDataStore = create<DataState>((set) => ({
  kpis: [],
  portfolio: null,
  watchlists: [],
  notifications: [],
  unreadNotifications: 0,
  setKpis: (kpis) => set({ kpis }),
  setPortfolio: (portfolio) => set({ portfolio }),
  setWatchlists: (watchlists) => set({ watchlists }),
  setNotifications: (notifications, unreadNotifications) =>
    set({ notifications, unreadNotifications }),
  markNotificationRead: (id) =>
    set((s) => ({
      notifications: s.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n,
      ),
      unreadNotifications: Math.max(0, s.unreadNotifications - 1),
    })),
}));

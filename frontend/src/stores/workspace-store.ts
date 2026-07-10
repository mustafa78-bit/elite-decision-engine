import { create } from "zustand";

export interface Panel {
  id: string;
  type: string;
  title: string;
  x: number;
  y: number;
  w: number;
  h: number;
  minimized: boolean;
}

interface SavedLayout {
  id: string;
  name: string;
  panels: Panel[];
  createdAt: number;
}

interface WorkspaceState {
  panels: Panel[];
  activePanelId: string | null;
  fullscreen: boolean;
  focusMode: boolean;
  sidebarCollapsed: boolean;
  savedLayouts: SavedLayout[];
  setSidebarCollapsed: (v: boolean) => void;
  toggleSidebar: () => void;
  setFullscreen: (v: boolean) => void;
  toggleFullscreen: () => void;
  setFocusMode: (v: boolean) => void;
  toggleFocusMode: () => void;
  setActivePanel: (id: string | null) => void;
  addPanel: (panel: Panel) => void;
  removePanel: (id: string) => void;
  minimizePanel: (id: string) => void;
  updatePanelPosition: (id: string, x: number, y: number) => void;
  updatePanelSize: (id: string, w: number, h: number) => void;
  clearPanels: () => void;
  saveWorkspace: (name?: string) => void;
  restoreWorkspace: () => void;
  loadLayout: (id: string) => void;
  deleteLayout: (id: string) => void;
}

const STORAGE_KEY = "elite-workspace";
const LAYOUTS_KEY = "elite-workspace-layouts";

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  panels: [],
  activePanelId: null,
  fullscreen: false,
  focusMode: false,
  sidebarCollapsed: false,
  savedLayouts: [],

  setSidebarCollapsed: (v) => set({ sidebarCollapsed: v }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setFullscreen: (v) => set({ fullscreen: v }),
  toggleFullscreen: () => set((s) => ({ fullscreen: !s.fullscreen })),
  setFocusMode: (v) => set({ focusMode: v }),
  toggleFocusMode: () => set((s) => ({ focusMode: !s.focusMode })),

  setActivePanel: (id) => set({ activePanelId: id }),

  addPanel: (panel) => set((s) => ({ panels: [...s.panels, panel] })),

  removePanel: (id) => set((s) => ({ panels: s.panels.filter((p) => p.id !== id) })),

  minimizePanel: (id) =>
    set((s) => ({
      panels: s.panels.map((p) =>
        p.id === id ? { ...p, minimized: !p.minimized } : p,
      ),
    })),

  updatePanelPosition: (id, x, y) =>
    set((s) => ({
      panels: s.panels.map((p) => (p.id === id ? { ...p, x, y } : p)),
    })),

  updatePanelSize: (id, w, h) =>
    set((s) => ({
      panels: s.panels.map((p) => (p.id === id ? { ...p, w, h } : p)),
    })),

  clearPanels: () => set({ panels: [] }),

  saveWorkspace: (name) => {
    const { panels, savedLayouts } = get();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(panels));
    if (name) {
      const layout: SavedLayout = {
        id: Date.now().toString(),
        name,
        panels: JSON.parse(JSON.stringify(panels)),
        createdAt: Date.now(),
      };
      const updated = [...savedLayouts, layout];
      set({ savedLayouts: updated });
      localStorage.setItem(LAYOUTS_KEY, JSON.stringify(updated));
    }
  },

  restoreWorkspace: () => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        set({ panels: JSON.parse(saved) });
      }
      const savedLayouts = localStorage.getItem(LAYOUTS_KEY);
      if (savedLayouts) {
        set({ savedLayouts: JSON.parse(savedLayouts) });
      }
    } catch {
      // ignore
    }
  },

  loadLayout: (id) => {
    try {
      const savedLayouts = get().savedLayouts;
      const layout = savedLayouts.find((l) => l.id === id);
      if (layout) {
        set({ panels: JSON.parse(JSON.stringify(layout.panels)) });
        localStorage.setItem(STORAGE_KEY, JSON.stringify(layout.panels));
      }
    } catch {
      // ignore
    }
  },

  deleteLayout: (id) => {
    const updated = get().savedLayouts.filter((l) => l.id !== id);
    set({ savedLayouts: updated });
    localStorage.setItem(LAYOUTS_KEY, JSON.stringify(updated));
  },
}));

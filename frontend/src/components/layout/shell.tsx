import { Outlet, Navigate } from "react-router-dom";
import Sidebar from "./sidebar";
import Topbar from "./topbar";
import { CommandPalette } from "./command-palette";
import { ToastProvider } from "./toast-provider";
import { GlobalSearch } from "../workspace/global-search";
import { OfflineIndicator } from "./offline-indicator";
import { useWorkspaceStore } from "../../stores/workspace-store";
import { cn } from "../../lib/utils";

export default function Shell() {
  const { sidebarCollapsed, focusMode, fullscreen } = useWorkspaceStore();

  if (fullscreen) {
    return (
      <div className="h-screen bg-[var(--bg-base)] text-[var(--text-primary)] overflow-hidden">
        <Topbar />
        <main className="h-[calc(100vh-2rem)] overflow-auto">
          <Outlet />
        </main>
        <ToastProvider />
      </div>
    );
  }

  if (focusMode) {
    return (
      <div className="h-screen flex flex-col bg-[var(--bg-base)] text-[var(--text-primary)] overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-y-auto p-5">
          <Outlet />
        </main>
        <CommandPalette />
        <GlobalSearch />
        <OfflineIndicator />
        <ToastProvider />
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-[var(--bg-base)] text-[var(--text-primary)] overflow-hidden">
      <OfflineIndicator />
      <Topbar />
      <div className="flex flex-1 overflow-hidden">
        <aside
          className={cn(
            "h-full border-r border-[var(--border-subtle)] shrink-0 overflow-y-auto transition-all duration-200",
            sidebarCollapsed ? "w-0 overflow-hidden" : "w-56",
          )}
        >
          {!sidebarCollapsed && <Sidebar />}
        </aside>
        <main className="flex-1 overflow-y-auto p-5">
          <Outlet />
        </main>
      </div>
      <CommandPalette />
      <GlobalSearch />
      <ToastProvider />
    </div>
  );
}

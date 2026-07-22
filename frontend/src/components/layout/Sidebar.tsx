import { NavLink, useLocation } from "react-router-dom";
import { cn } from "../../lib/utils";
import {
  LayoutDashboard,
  Zap,
  TrendingUp,
  Briefcase,
  ShieldAlert,
  BookOpen,
  FileText,
  Settings,
} from "lucide-react";

interface SidebarItem {
  label: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
}

const sidebarItems: SidebarItem[] = [
  { label: "Overview", path: "/overview", icon: LayoutDashboard },
  { label: "Signals", path: "/signals", icon: Zap },
  { label: "Markets", path: "/market", icon: TrendingUp },
  { label: "Portfolio", path: "/portfolio", icon: Briefcase },
  { label: "Risk", path: "/risk", icon: ShieldAlert },
  { label: "Research", path: "/intelligence", icon: BookOpen },
  { label: "Journal", path: "/trades", icon: FileText },
  { label: "Settings", path: "/preferences", icon: Settings },
];

export default function Sidebar() {
  const { pathname } = useLocation();

  return (
    <aside className="w-[240px] h-full flex flex-col bg-white border-r border-slate-200 shrink-0 select-none">
      <div className="h-16 px-6 flex items-center border-b border-slate-200">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded bg-blue-600 flex items-center justify-center text-white font-bold text-sm tracking-wider">
            E
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-semibold text-slate-900 tracking-tight">
              Elite Intelligence
            </span>
            <span className="text-[10px] text-slate-400 font-medium tracking-wider uppercase leading-none">
              Institutional Core
            </span>
          </div>
        </div>
      </div>

      <nav className="flex-1 py-6 px-4 space-y-1.5">
        {sidebarItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname.startsWith(item.path);

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150",
                isActive
                  ? "bg-blue-50 text-blue-600 font-semibold"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              )}
            >
              <Icon className={cn("w-4 h-4 shrink-0", isActive ? "text-blue-600" : "text-slate-400")} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-100">
        <div className="flex items-center gap-2.5 px-2 py-1.5 rounded-lg bg-slate-50">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
          <span className="text-xs text-slate-500 font-medium font-mono tracking-tight">
            SECURE CONNECTED
          </span>
        </div>
      </div>
    </aside>
  );
}

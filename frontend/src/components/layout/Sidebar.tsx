import { NavLink } from "react-router-dom";
import { cn } from "../../lib/utils";

interface NavItem {
  label: string;
  path: string;
  icon: string;
}

const sections: { title: string; items: NavItem[] }[] = [
  {
    title: "Overview",
    items: [
      { label: "Dashboard", path: "/dashboard", icon: "◈" },
      { label: "Portfolio", path: "/portfolio", icon: "▣" },
      { label: "Scanner", path: "/scanner", icon: "◎" },
      { label: "Trade Journal", path: "/trades", icon: "⇄" },
      { label: "Paper Trading", path: "/paper-trading", icon: "◻" },
    ],
  },
  {
    title: "Intelligence",
    items: [
      { label: "Signals", path: "/signals", icon: "⚡" },
      { label: "Decision Center", path: "/decisions", icon: "◈" },
      { label: "Analytics", path: "/analytics", icon: "▦" },
      { label: "Market", path: "/market", icon: "◉" },
      { label: "Risk", path: "/risk", icon: "▲" },
      { label: "Regime", path: "/regime", icon: "◆" },
    ],
  },
  {
    title: "Data",
    items: [
      { label: "Intelligence", path: "/intelligence", icon: "✦" },
      { label: "Funding", path: "/funding", icon: "◎" },
      { label: "Open Interest", path: "/open-interest", icon: "◐" },
      { label: "Whale Activity", path: "/whale", icon: "◉" },
      { label: "Liquidity", path: "/liquidity", icon: "≈" },
    ],
  },
  {
    title: "System",
    items: [
      { label: "Notifications", path: "/notifications", icon: "🔔" },
      { label: "Timeline", path: "/timeline", icon: "≡" },
      { label: "Watchlists", path: "/watchlists", icon: "☰" },
      { label: "Settings", path: "/preferences", icon: "⚙" },
      { label: "Profile", path: "/profile", icon: "👤" },
    ],
  },
];

export default function Sidebar() {
  return (
    <aside className="w-56 h-full flex flex-col bg-[var(--bg-base)] border-r border-[var(--border-subtle)] shrink-0 overflow-y-auto">
      <nav className="flex-1 py-4 px-2 space-y-4">
        {sections.map((section) => (
          <div key={section.title}>
            <div className="px-2 mb-1">
              <span className="text-[9px] font-medium text-[var(--text-muted)] uppercase tracking-[0.12em]">
                {section.title}
              </span>
            </div>
            {section.items.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-[var(--transition-fast)]",
                    isActive
                      ? "text-[var(--text-primary)] bg-[var(--bg-hover)]"
                      : "text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]",
                  )
                }
              >
                <span className="w-4 text-center text-[11px]">{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="px-4 py-3 border-t border-[var(--border-subtle)]">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-green)]" />
          <span className="text-[10px] text-[var(--text-muted)] font-mono">
            System Online
          </span>
        </div>
      </div>
    </aside>
  );
}

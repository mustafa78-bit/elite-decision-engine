import { NavLink, useLocation } from "react-router-dom";
import { cn } from "../../lib/utils";

const roomMap: Record<string, string> = {
  '/command-deck': '#2563EB',
  '/portfolio': '#ea580c',
  '/scanner': '#10B981',
  '/trades': '#ef4444',
  '/timeline': '#ef4444',
  '/journal': '#ef4444',
  '/signals': '#7c3aed',
  '/decisions': '#7c3aed',
  '/intelligence': '#7c3aed',
  '/ai-experience': '#7c3aed',
  '/regime': '#7c3aed',
  '/funding': '#10B981',
  '/open-interest': '#10B981',
  '/risk': '#ef4444',
  '/analytics': '#4f46e5',
  '/backtest': '#4f46e5',
  '/hero-dashboard': '#4f46e5',
  '/execution': '#0891b2',
  '/paper-trading': '#0891b2',
  '/trading-workspace': '#0891b2',
  '/trading-control': '#0891b2',
  '/market': '#0891b2',
  '/watchlists': '#0891b2',
  '/profile': '#4f46e5',
  '/preferences': '#4f46e5',
};

function getRoomColor(pathname: string): string {
  for (const [prefix, color] of Object.entries(roomMap)) {
    if (pathname.startsWith(prefix)) return color;
  }
  return '#2563EB';
}

interface NavItem {
  label: string;
  path: string;
  icon: string;
}

const sections: { title: string; subtitle: string; items: NavItem[] }[] = [
  {
    title: "Command Deck",
    subtitle: "Headquarters",
    items: [
      { label: "Command Deck", path: "/command-deck", icon: "◈" },
      { label: "Dashboard", path: "/dashboard", icon: "▣" },
      { label: "Overview", path: "/overview", icon: "◉" },
    ],
  },
  {
    title: "Scanner Room",
    subtitle: "Asset Surveillance",
    items: [
      { label: "Scanner", path: "/scanner", icon: "◎" },
      { label: "Market", path: "/market", icon: "◉" },
      { label: "Watchlists", path: "/watchlists", icon: "☰" },
    ],
  },
  {
    title: "AI Council Chamber",
    subtitle: "Decision Intelligence",
    items: [
      { label: "Decision Center", path: "/decisions", icon: "◈" },
      { label: "Signals", path: "/signals", icon: "⚡" },
      { label: "Intelligence", path: "/intelligence", icon: "✦" },
      { label: "AI Experience", path: "/ai-experience", icon: "◆" },
    ],
  },
  {
    title: "Risk Operations",
    subtitle: "Risk & Exposure",
    items: [
      { label: "Risk Control", path: "/risk", icon: "▲" },
      { label: "Regime", path: "/regime", icon: "◆" },
    ],
  },
  {
    title: "Portfolio Vault",
    subtitle: "Capital Management",
    items: [
      { label: "Portfolio", path: "/portfolio", icon: "▣" },
    ],
  },
  {
    title: "Capital Flow",
    subtitle: "Market Intelligence",
    items: [
      { label: "Funding", path: "/funding", icon: "◎" },
      { label: "Open Interest", path: "/open-interest", icon: "◐" },
    ],
  },
  {
    title: "Mission Archive",
    subtitle: "Records & Journal",
    items: [
      { label: "Trade Journal", path: "/trades", icon: "⇄" },
      { label: "Timeline", path: "/timeline", icon: "≡" },
      { label: "Journal", path: "/journal", icon: "≡" },
      { label: "Notifications", path: "/notifications", icon: "⏏" },
    ],
  },
  {
    title: "System Core",
    subtitle: "Operations & Config",
    items: [
      { label: "Analytics", path: "/analytics", icon: "▦" },
      { label: "Backtest", path: "/backtest", icon: "◻" },
      { label: "Execution", path: "/execution", icon: "≡" },
      { label: "Paper Trading", path: "/paper-trading", icon: "◻" },
      { label: "Preferences", path: "/preferences", icon: "⚙" },
      { label: "Profile", path: "/profile", icon: "⏏" },
    ],
  },
];

export default function Sidebar() {
  const { pathname } = useLocation();
  const activeRoomColor = getRoomColor(pathname);

  return (
    <aside className="w-56 h-full flex flex-col bg-white border-r border-[var(--border-default)] shrink-0 overflow-y-auto">
      <div className="px-5 py-4 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2.5">
          <span
            className="w-2.5 h-2.5 rounded-full transition-all duration-500"
            style={{
              backgroundColor: activeRoomColor,
              boxShadow: `0 0 10px ${activeRoomColor}60`,
            }}
          />
          <span className="text-sm font-semibold text-[var(--text-primary)] tracking-tight">
            Elite HQ
          </span>
        </div>
        <p className="text-[9px] text-[var(--text-muted)] mt-1 font-mono uppercase tracking-[0.12em] font-semibold">
          Decision Intelligence
        </p>
      </div>

      <nav className="flex-1 py-4 px-2.5 space-y-5">
        {sections.map((section) => {
          const isSectionActive = section.items.some((it) => pathname.startsWith(it.path));
          return (
            <div key={section.title} className="space-y-1">
              <div className="px-2 mb-1.5 flex items-center gap-2">
                <span
                  className="w-0.5 h-3 rounded-full transition-opacity duration-500"
                  style={{
                    backgroundColor: isSectionActive ? activeRoomColor : 'transparent',
                    opacity: isSectionActive ? 1 : 0.2,
                  }}
                />
                <div className="min-w-0">
                  <div className="text-[10px] font-bold text-[var(--text-primary)] uppercase tracking-[0.08em] opacity-80 leading-tight">
                    {section.title}
                  </div>
                  <div className="text-[8px] text-[var(--text-muted)] font-mono uppercase tracking-[0.05em] opacity-80 mt-0.5">
                    {section.subtitle}
                  </div>
                </div>
              </div>
              <div className="space-y-0.5">
                {section.items.map((item) => {
                  const itemColor = getRoomColor(item.path);
                  const isActive = pathname.startsWith(item.path);

                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      className={cn(
                        "flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200",
                        isActive
                          ? "text-[var(--text-primary)] font-semibold"
                          : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]",
                      )}
                      style={isActive ? {
                        backgroundColor: `${activeRoomColor}0a`,
                        borderLeft: `2.5px solid ${activeRoomColor}`,
                      } : {}}
                      aria-current={isActive ? "page" : undefined}
                    >
                      <span
                        className="w-4 text-center text-[12px] transition-colors duration-300"
                        style={{ color: isActive ? itemColor : '#64748b' }}
                      >
                        {item.icon}
                      </span>
                      <span>{item.label}</span>
                    </NavLink>
                  );
                })}
              </div>
            </div>
          );
        })}
      </nav>

      <div className="px-5 py-3.5 border-t border-[var(--border-subtle)] bg-slate-50/50">
        <div className="flex items-center gap-2">
          <span
            className="w-2 h-2 rounded-full"
            style={{
              backgroundColor: activeRoomColor,
              boxShadow: `0 0 8px ${activeRoomColor}80`,
              animation: 'sidebar-pulse 2.5s ease-in-out infinite',
            }}
          />
          <span className="text-[10px] text-[var(--text-secondary)] font-mono font-medium">
            System Operational
          </span>
        </div>
      </div>

      <style>{`
        @keyframes sidebar-pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(0.9); }
        }
      `}</style>
    </aside>
  );
}

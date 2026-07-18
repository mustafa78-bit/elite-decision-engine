import { NavLink, useLocation } from "react-router-dom";
import { cn } from "../../lib/utils";

const roomMap: Record<string, string> = {
  '/command-deck': '#2563EB',
  '/portfolio': '#3B82F6',
  '/scanner': '#06B6D4',
  '/trades': '#F59E0B',
  '/timeline': '#F59E0B',
  '/journal': '#F59E0B',
  '/signals': '#8B5CF6',
  '/decisions': '#8B5CF6',
  '/intelligence': '#8B5CF6',
  '/ai-experience': '#8B5CF6',
  '/regime': '#8B5CF6',
  '/funding': '#10B981',
  '/open-interest': '#10B981',
  '/risk': '#F43F5E',
  '/analytics': '#6366F1',
  '/backtest': '#6366F1',
  '/hero-dashboard': '#6366F1',
  '/execution': '#14B8A6',
  '/paper-trading': '#14B8A6',
  '/trading-workspace': '#14B8A6',
  '/trading-control': '#14B8A6',
  '/market': '#0EA5E9',
  '/watchlists': '#0EA5E9',
  '/profile': '#6366F1',
  '/preferences': '#6366F1',
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
    <aside className="w-56 h-full flex flex-col bg-[var(--bg-base)] border-r border-[var(--border-subtle)] shrink-0 overflow-y-auto">
      <div className="px-4 py-4 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2">
          <span
            className="w-2 h-2 rounded-full transition-colors duration-500"
            style={{
              backgroundColor: activeRoomColor,
              boxShadow: `0 0 8px ${activeRoomColor}`,
            }}
          />
          <span className="text-sm font-semibold text-[var(--text-primary)] tracking-tight">
            Elite HQ
          </span>
        </div>
        <p className="text-[10px] text-[var(--text-muted)] mt-1 font-mono uppercase tracking-[0.1em]">
          Decision Intelligence
        </p>
      </div>

      <nav className="flex-1 py-3 px-2 space-y-4">
        {sections.map((section) => {
          const isSectionActive = section.items.some((it) => pathname.startsWith(it.path));
          return (
            <div key={section.title}>
              <div className="px-2 mb-1 flex items-center gap-2">
                <span
                  className="w-1 h-3 rounded-full transition-opacity duration-500"
                  style={{
                    backgroundColor: isSectionActive ? activeRoomColor : 'transparent',
                    opacity: isSectionActive ? 1 : 0.3,
                  }}
                />
                <div className="min-w-0">
                  <div className="text-[9px] font-medium text-[var(--text-muted)] uppercase tracking-[0.12em] leading-tight">
                    {section.title}
                  </div>
                  <div className="text-[7px] text-[var(--text-muted)] font-mono uppercase tracking-[0.08em] opacity-50">
                    {section.subtitle}
                  </div>
                </div>
              </div>
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
                        ? "text-[var(--text-primary)]"
                        : "text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]",
                    )}
                    style={isActive ? {
                      backgroundColor: `${activeRoomColor}15`,
                      borderLeft: `2px solid ${activeRoomColor}`,
                      boxShadow: `inset 0 0 20px ${activeRoomColor}08`,
                    } : {}}
                    aria-current={isActive ? "page" : undefined}
                  >
                    <span
                      className="w-4 text-center text-[11px] transition-colors duration-300"
                      style={{ color: isActive ? itemColor : undefined }}
                    >
                      {item.icon}
                    </span>
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </div>
          );
        })}
      </nav>

      <div className="px-4 py-3 border-t border-[var(--border-subtle)]">
        <div className="flex items-center gap-2">
          <span
            className="w-1.5 h-1.5 rounded-full"
            style={{
              backgroundColor: activeRoomColor,
              boxShadow: `0 0 6px ${activeRoomColor}`,
              animation: 'sidebar-pulse 2s ease-in-out infinite',
            }}
          />
          <span className="text-[10px] text-[var(--text-muted)] font-mono">
            System Online
          </span>
        </div>
      </div>

      <style>{`
        @keyframes sidebar-pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
      `}</style>
    </aside>
  );
}

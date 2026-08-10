import { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { cn } from "../../lib/utils";

interface NavItem {
  labelKey: string;
  path: string;
  icon: string;
}

interface NavSection {
  key: string;
  titleKey: string;
  subtitleKey: string;
  icon: string;
  accent: string;
  items: NavItem[];
}

const sections: NavSection[] = [
  {
    key: "commandDeck",
    titleKey: "nav.section.commandDeck.title",
    subtitleKey: "nav.section.commandDeck.subtitle",
    icon: "◈",
    accent: "#e6a94f",
    items: [
      { labelKey: "nav.item.commandDeck", path: "/command-deck", icon: "◈" },
      { labelKey: "nav.item.dashboard", path: "/dashboard", icon: "▣" },
      { labelKey: "nav.item.overview", path: "/overview", icon: "◉" },
    ],
  },
  {
    key: "scannerRoom",
    titleKey: "nav.section.scannerRoom.title",
    subtitleKey: "nav.section.scannerRoom.subtitle",
    icon: "◎",
    accent: "#5b9bf6",
    items: [
      { labelKey: "nav.item.scanner", path: "/scanner", icon: "◎" },
      { labelKey: "nav.item.market", path: "/market", icon: "◉" },
      { labelKey: "nav.item.watchlists", path: "/watchlists", icon: "☰" },
    ],
  },
  {
    key: "aiCouncilChamber",
    titleKey: "nav.section.aiCouncilChamber.title",
    subtitleKey: "nav.section.aiCouncilChamber.subtitle",
    icon: "✦",
    accent: "#45d6c4",
    items: [
      { labelKey: "nav.item.decisions", path: "/decisions", icon: "◈" },
      { labelKey: "nav.item.signals", path: "/signals", icon: "⚡" },
      { labelKey: "nav.item.intelligence", path: "/intelligence", icon: "✦" },
    ],
  },
  {
    key: "riskOperations",
    titleKey: "nav.section.riskOperations.title",
    subtitleKey: "nav.section.riskOperations.subtitle",
    icon: "▲",
    accent: "#f5697a",
    items: [
      { labelKey: "nav.item.risk", path: "/risk", icon: "▲" },
      { labelKey: "nav.item.regime", path: "/regime", icon: "◆" },
    ],
  },
  {
    key: "portfolioVault",
    titleKey: "nav.section.portfolioVault.title",
    subtitleKey: "nav.section.portfolioVault.subtitle",
    icon: "▣",
    accent: "#a98af5",
    items: [
      { labelKey: "nav.item.portfolio", path: "/portfolio", icon: "▣" },
    ],
  },
  {
    key: "capitalFlow",
    titleKey: "nav.section.capitalFlow.title",
    subtitleKey: "nav.section.capitalFlow.subtitle",
    icon: "◉",
    accent: "#f5985a",
    items: [
      { labelKey: "nav.item.funding", path: "/funding", icon: "◎" },
      { labelKey: "nav.item.openInterest", path: "/open-interest", icon: "◐" },
    ],
  },
  {
    key: "missionArchive",
    titleKey: "nav.section.missionArchive.title",
    subtitleKey: "nav.section.missionArchive.subtitle",
    icon: "≡",
    accent: "#4ddb92",
    items: [
      { labelKey: "nav.item.trades", path: "/trades", icon: "⇄" },
      { labelKey: "nav.item.timeline", path: "/timeline", icon: "≡" },
      { labelKey: "nav.item.journal", path: "/journal", icon: "≡" },
      { labelKey: "nav.item.notifications", path: "/notifications", icon: "⏏" },
    ],
  },
  {
    key: "systemCore",
    titleKey: "nav.section.systemCore.title",
    subtitleKey: "nav.section.systemCore.subtitle",
    icon: "⚙",
    accent: "#6366F1",
    items: [
      { labelKey: "nav.item.analytics", path: "/analytics", icon: "▦" },
      { labelKey: "nav.item.backtest", path: "/backtest", icon: "◻" },
      { labelKey: "nav.item.execution", path: "/execution", icon: "≡" },
      { labelKey: "nav.item.paperTrading", path: "/paper-trading", icon: "◻" },
      { labelKey: "nav.item.preferences", path: "/preferences", icon: "⚙" },
      { labelKey: "nav.item.profile", path: "/profile", icon: "⏏" },
    ],
  },
];

function findActiveSectionKey(pathname: string): string {
  for (const section of sections) {
    if (section.items.some((it) => pathname.startsWith(it.path))) return section.key;
  }
  return sections[0].key;
}

export default function Sidebar() {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  const activeSectionKey = findActiveSectionKey(pathname);
  const [openSection, setOpenSection] = useState<string>(activeSectionKey);
  const activeAccent = sections.find((s) => s.key === activeSectionKey)?.accent ?? "#5b9bf6";

  return (
    <aside className="w-72 h-full flex flex-col bg-[var(--bg-base)] border-r border-[var(--border-subtle)] shrink-0 overflow-y-auto">
      <div className="px-4 py-4 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2">
          <span
            className="w-2.5 h-2.5 rounded-full transition-colors duration-500"
            style={{
              backgroundColor: activeAccent,
              boxShadow: `0 0 8px ${activeAccent}`,
            }}
          />
          <span className="text-base font-semibold text-[var(--text-primary)] tracking-tight">
            Elite HQ
          </span>
        </div>
        <p className="text-[11px] text-[var(--text-muted)] mt-1 font-mono uppercase tracking-[0.1em]">
          {t("nav.brandSubtitle")}
        </p>
      </div>

      <nav className="flex-1 py-3 px-2 space-y-1">
        {sections.map((section) => {
          const isSectionActive = section.key === activeSectionKey;
          const isOpen = section.key === openSection;

          return (
            <div key={section.key}>
              <button
                type="button"
                onClick={() => setOpenSection(isOpen ? "" : section.key)}
                className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left transition-colors duration-150 hover:bg-[var(--bg-hover)]"
              >
                <span
                  className="w-7 h-7 rounded-md flex items-center justify-center text-[14px] shrink-0 transition-colors duration-300"
                  style={{
                    backgroundColor: `${section.accent}1c`,
                    color: section.accent,
                  }}
                >
                  {section.icon}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="text-[13px] font-semibold text-[var(--text-primary)] leading-tight truncate">
                    {t(section.titleKey)}
                  </div>
                  <div className="text-[10.5px] text-[var(--text-muted)] font-mono uppercase tracking-[0.06em] opacity-60 truncate">
                    {t(section.subtitleKey)}
                  </div>
                </div>
                {isSectionActive && (
                  <span
                    className="w-1.5 h-1.5 rounded-full shrink-0"
                    style={{ backgroundColor: section.accent, boxShadow: `0 0 6px ${section.accent}` }}
                  />
                )}
                <span
                  className="text-[11px] text-[var(--text-muted)] shrink-0 transition-transform duration-200"
                  style={{ transform: isOpen ? "rotate(90deg)" : "rotate(0deg)" }}
                >
                  ▸
                </span>
              </button>

              <div
                className="grid transition-[grid-template-rows] duration-200 ease-out"
                style={{ gridTemplateRows: isOpen ? "1fr" : "0fr" }}
              >
                <div className="overflow-hidden">
                  <div className="pt-1 pb-2 space-y-0.5">
                    {section.items.map((item) => {
                      const isActive = pathname.startsWith(item.path);

                      return (
                        <NavLink
                          key={item.path}
                          to={item.path}
                          className={cn(
                            "flex items-center gap-2.5 pl-9 pr-3 py-1.5 rounded-lg text-[13.5px] font-medium transition-all duration-200",
                            isActive
                              ? "text-[var(--text-primary)]"
                              : "text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]",
                          )}
                          style={isActive ? {
                            backgroundColor: `${section.accent}15`,
                            borderLeft: `2px solid ${section.accent}`,
                            boxShadow: `inset 0 0 20px ${section.accent}08`,
                          } : {}}
                          aria-current={isActive ? "page" : undefined}
                        >
                          <span
                            className="w-4 text-center text-[13px] transition-colors duration-300"
                            style={{ color: isActive ? section.accent : undefined }}
                          >
                            {item.icon}
                          </span>
                          <span>{t(item.labelKey)}</span>
                        </NavLink>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </nav>

      <div className="px-4 py-3 border-t border-[var(--border-subtle)]">
        <div className="flex items-center gap-2">
          <span
            className="w-1.5 h-1.5 rounded-full"
            style={{
              backgroundColor: activeAccent,
              boxShadow: `0 0 6px ${activeAccent}`,
              animation: 'sidebar-pulse 2s ease-in-out infinite',
            }}
          />
          <span className="text-[11px] text-[var(--text-muted)] font-mono">
            {t("nav.systemOnline")}
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

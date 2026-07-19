import { useState } from "react"
import { NavLink, useLocation, useNavigate } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"

interface MobileNavItem {
  label: string
  path: string
  icon: string
  color: string
}

const primaryItems: MobileNavItem[] = [
  { label: "Command", path: "/command-deck", icon: "◈", color: "#2563EB" },
  { label: "Scanner", path: "/scanner", icon: "◎", color: "#06B6D4" },
  { label: "Decisions", path: "/decisions", icon: "⚡", color: "#8B5CF6" },
  { label: "Portfolio", path: "/portfolio", icon: "▣", color: "#3B82F6" },
]

const moreItems = [
  { label: "Overview", path: "/overview", icon: "◉", color: "#2563EB" },
  { label: "Market", path: "/market", icon: "◉", color: "#0EA5E9" },
  { label: "Watchlists", path: "/watchlists", icon: "☰", color: "#0EA5E9" },
  { label: "Signals", path: "/signals", icon: "⚡", color: "#8B5CF6" },
  { label: "Intelligence", path: "/intelligence", icon: "✦", color: "#8B5CF6" },
  { label: "AI Experience", path: "/ai-experience", icon: "◆", color: "#8B5CF6" },
  { label: "Risk Control", path: "/risk", icon: "▲", color: "#F43F5E" },
  { label: "Regime", path: "/regime", icon: "◆", color: "#8B5CF6" },
  { label: "Funding", path: "/funding", icon: "◎", color: "#10B981" },
  { label: "Open Interest", path: "/open-interest", icon: "◐", color: "#10B981" },
  { label: "Trade Journal", path: "/trades", icon: "⇄", color: "#F59E0B" },
  { label: "Timeline", path: "/timeline", icon: "≡", color: "#F59E0B" },
  { label: "Journal", path: "/journal", icon: "≡", color: "#F59E0B" },
  { label: "Analytics", path: "/analytics", icon: "▦", color: "#6366F1" },
  { label: "Backtest", path: "/backtest", icon: "◻", color: "#6366F1" },
  { label: "Execution", path: "/execution", icon: "≡", color: "#14B8A6" },
  { label: "Paper Trading", path: "/paper-trading", icon: "◻", color: "#14B8A6" },
  { label: "Preferences", path: "/preferences", icon: "⚙", color: "#6366F1" },
  { label: "Profile", path: "/profile", icon: "⏏", color: "#6366F1" },
]

export default function MobileNav() {
  const [isOpen, setIsOpen] = useState(false)
  const { pathname } = useLocation()
  const navigate = useNavigate()

  const handleMoreClick = () => {
    setIsOpen(!isOpen)
  }

  const isMoreActive = !primaryItems.some((item) => pathname.startsWith(item.path))

  return (
    <>
      {/* Floating Glassmorphism Bottom Tab Bar */}
      <nav
        className="fixed bottom-0 left-0 right-0 z-40 md:hidden border-t border-[var(--border-subtle)] backdrop-blur-md bg-[var(--bg-base)]/90"
        style={{
          height: "64px",
          paddingBottom: "safe-area-inset-bottom",
        }}
      >
        <div className="flex h-full items-center justify-around px-2">
          {primaryItems.map((item) => {
            const isActive = pathname.startsWith(item.path)
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setIsOpen(false)}
                className="flex flex-col items-center justify-center relative flex-1"
                style={{ height: "48px", minWidth: "48px" }}
              >
                <span
                  className="text-lg transition-colors duration-200"
                  style={{ color: isActive ? item.color : "var(--text-muted)" }}
                >
                  {item.icon}
                </span>
                <span
                  className="text-[9px] font-medium mt-0.5 tracking-wider font-mono transition-colors duration-200"
                  style={{ color: isActive ? "var(--text-primary)" : "var(--text-muted)" }}
                >
                  {item.label}
                </span>
                {isActive && (
                  <motion.div
                    layoutId="activeTabDot"
                    className="absolute bottom-1 w-1 h-1 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                )}
              </NavLink>
            )
          })}

          {/* More Trigger */}
          <button
            onClick={handleMoreClick}
            className="flex flex-col items-center justify-center relative flex-1 cursor-pointer"
            style={{ height: "48px", minWidth: "48px" }}
          >
            <span
              className="text-lg transition-colors duration-200"
              style={{ color: isMoreActive || isOpen ? "var(--accent-blue)" : "var(--text-muted)" }}
            >
              ☰
            </span>
            <span
              className="text-[9px] font-medium mt-0.5 tracking-wider font-mono transition-colors duration-200"
              style={{ color: isMoreActive || isOpen ? "var(--text-primary)" : "var(--text-muted)" }}
            >
              More
            </span>
            {(isMoreActive || isOpen) && (
              <motion.div
                layoutId="activeTabDot"
                className="absolute bottom-1 w-1 h-1 rounded-full"
                style={{ backgroundColor: "var(--accent-blue)" }}
              />
            )}
          </button>
        </div>
      </nav>

      {/* Slide-Up Bottom Sheet Drawer for "More" options */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.4 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 bg-black z-40 md:hidden"
            />

            {/* Bottom Sheet */}
            <motion.div
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 220 }}
              className="fixed bottom-[64px] left-0 right-0 z-50 md:hidden bg-[var(--bg-base)] border-t border-[var(--border-subtle)] rounded-t-2xl shadow-xl overflow-hidden max-h-[70vh] flex flex-col"
            >
              {/* Drag handle */}
              <div className="flex justify-center py-3 shrink-0">
                <div className="w-12 h-1 bg-gray-600 rounded-full opacity-40" />
              </div>

              <div className="flex items-center justify-between px-5 pb-3 border-b border-[var(--border-subtle)] shrink-0">
                <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-primary)] font-mono">
                  All Terminals & Chambers
                </span>
                <button
                  onClick={() => setIsOpen(false)}
                  className="w-8 h-8 rounded-full border border-[var(--border-subtle)] flex items-center justify-center text-sm font-mono text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                >
                  ✕
                </button>
              </div>

              {/* Grid of rooms */}
              <div className="flex-1 overflow-y-auto p-4 grid grid-cols-3 gap-3">
                {moreItems.map((item) => {
                  const isActive = pathname.startsWith(item.path)
                  return (
                    <button
                      key={item.path}
                      onClick={() => {
                        setIsOpen(false)
                        navigate(item.path)
                      }}
                      className="flex flex-col items-center justify-center p-3 rounded-xl border transition-all duration-200 text-center"
                      style={{
                        minHeight: "80px",
                        backgroundColor: isActive ? `${item.color}10` : "transparent",
                        borderColor: isActive ? item.color : "var(--border-subtle)",
                      }}
                    >
                      <span
                        className="text-lg mb-1"
                        style={{ color: isActive ? item.color : "var(--text-muted)" }}
                      >
                        {item.icon}
                      </span>
                      <span
                        className="text-[9px] font-medium leading-tight font-mono uppercase tracking-wider"
                        style={{ color: isActive ? "var(--text-primary)" : "var(--text-muted)" }}
                      >
                        {item.label}
                      </span>
                    </button>
                  )
                })}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  )
}

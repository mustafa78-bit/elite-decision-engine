import { NavLink } from "react-router-dom";

const items = [
  { label: "Overview", path: "/overview" },
  { label: "Dashboard", path: "/dashboard" },
  { label: "Trades", path: "/trades" },
  { label: "Market", path: "/market" },
  { label: "Signals", path: "/signals" },
  { label: "Risk", path: "/risk" },
  { label: "Regime", path: "/regime" },
  { label: "Analytics", path: "/analytics" },
  { label: "Portfolio", path: "/portfolio" },
  { label: "Paper Trading", path: "/paper-trading" },
  { label: "Notifications", path: "/notifications" },
  { label: "Execution", path: "/execution" },
  { label: "Intelligence", path: "/intelligence" },
];

export default function Sidebar() {
  return (
    <aside className="w-44 border-r border-gray-800 bg-gray-950 flex flex-col shrink-0">
      <nav className="flex flex-col py-2">
        {items.map(({ label, path }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `text-left px-4 py-1.5 text-xs uppercase tracking-wider transition-colors ${
                isActive
                  ? "text-gray-100 bg-gray-900"
                  : "text-gray-500 hover:text-gray-200 hover:bg-gray-900"
              }`
            }
          >
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

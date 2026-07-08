const items = [
  "Dashboard",
  "Live Trades",
  "Signals",
  "Risk",
  "Analytics",
  "Settings",
];

export default function Sidebar() {
  return (
    <aside className="w-44 border-r border-gray-800 bg-gray-950 flex flex-col shrink-0">
      <nav className="flex flex-col py-2">
        {items.map((label) => (
          <button
            key={label}
            className="text-left px-4 py-1.5 text-xs text-gray-500 hover:text-gray-200 hover:bg-gray-900 transition-colors uppercase tracking-wider"
          >
            {label}
          </button>
        ))}
      </nav>
    </aside>
  );
}

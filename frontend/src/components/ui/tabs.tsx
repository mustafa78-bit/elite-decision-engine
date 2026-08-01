import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

interface Tab {
  id: string;
  label: string;
  content: ReactNode;
}

interface TabsProps {
  tabs: Tab[];
  defaultTab?: string;
  className?: string;
  onChange?: (id: string) => void;
}

export function Tabs({ tabs, defaultTab, className, onChange }: TabsProps) {
  const [active, setActive] = useState(defaultTab || tabs[0]?.id);

  useEffect(() => {
    if (defaultTab) {
      setActive(defaultTab);
    } else if (tabs.length > 0 && !tabs.find((t) => t.id === active)) {
      setActive(tabs[0].id);
    }
  }, [tabs, defaultTab, active]);

  return (
    <div className={cn("flex flex-col", className)}>
      <div className="flex border-b border-[var(--border-subtle)]">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              setActive(tab.id);
              onChange?.(tab.id);
            }}
            className={cn(
              "px-4 py-2 text-xs font-medium transition-colors relative",
              active === tab.id
                ? "text-[var(--text-primary)]"
                : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]",
            )}
          >
            {tab.label}
            {active === tab.id && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--accent-blue)]" />
            )}
          </button>
        ))}
      </div>
      <div className="pt-3">
        {tabs.find((t) => t.id === active)?.content}
      </div>
    </div>
  );
}

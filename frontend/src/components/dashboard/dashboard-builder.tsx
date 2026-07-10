import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "../ui/button";
import { useWidgetRegistry, type WidgetDefinition } from "./widget-registry";
import { cn } from "../../lib/utils";
import { useWorkspaceStore } from "../../stores/workspace-store";

export function DashboardBuilder() {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const { getAllWidgets, searchWidgets, getWidgetsByCategory } = useWidgetRegistry();
  const { addPanel } = useWorkspaceStore();

  const categories = ["all", "kpi", "portfolio", "risk", "monitoring", "ai", "notification", "chart", "market"];

  const widgets = selectedCategory === "all"
    ? search ? searchWidgets(search) : getAllWidgets()
    : search
      ? getWidgetsByCategory(selectedCategory as WidgetDefinition["category"]).filter(
          (w) => w.name.toLowerCase().includes(search.toLowerCase()),
        )
      : getWidgetsByCategory(selectedCategory as WidgetDefinition["category"]);

  const handleAddWidget = useCallback(
    (widget: WidgetDefinition) => {
      addPanel({
        id: `widget-${widget.id}-${Date.now()}`,
        type: widget.component,
        title: widget.name,
        x: 100 + Math.random() * 200,
        y: 100 + Math.random() * 200,
        w: widget.defaultWidth * 300,
        h: widget.defaultHeight * 200,
        minimized: false,
      });
    },
    [addPanel],
  );

  return (
    <>
      <Button
        variant="glass"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="text-[10px]"
      >
        {isOpen ? "Close Builder" : "Dashboard Builder"}
      </Button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
            onClick={() => setIsOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
              className="w-[800px] max-h-[80vh] rounded-2xl border border-[var(--border-default)] bg-[var(--bg-elevated)] backdrop-blur-2xl shadow-2xl overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-4 border-b border-[var(--border-subtle)]">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-sm font-medium text-[var(--text-primary)]">
                    Dashboard Builder
                  </h2>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                  >
                    ✕
                  </button>
                </div>
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search widgets..."
                  className="w-full bg-[var(--bg-base)] rounded-lg px-3 py-1.5 text-xs font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] border border-[var(--border-default)] focus:outline-none focus:border-[var(--accent-blue)]"
                />
                <div className="flex gap-1 mt-2">
                  {categories.map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setSelectedCategory(cat)}
                      className={cn(
                        "px-2 py-1 rounded-lg text-[9px] font-mono uppercase tracking-wider transition-all",
                        selectedCategory === cat
                          ? "bg-[var(--accent-blue)]/10 text-[var(--accent-blue)] border border-[var(--accent-blue)]/20"
                          : "text-[var(--text-muted)] hover:text-[var(--text-secondary)] border border-transparent",
                      )}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              </div>
              <div className="p-4 overflow-y-auto max-h-[50vh]">
                <div className="grid grid-cols-3 gap-2">
                  {widgets.map((widget) => (
                    <motion.div
                      key={widget.id}
                      layout
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="p-3 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)] hover:border-[var(--accent-blue)]/30 transition-all cursor-pointer"
                      onClick={() => handleAddWidget(widget)}
                    >
                      <div className="text-[10px] font-mono font-medium text-[var(--text-primary)]">
                        {widget.name}
                      </div>
                      <div className="text-[9px] text-[var(--text-muted)] mt-0.5">
                        {widget.description}
                      </div>
                      <div className="flex gap-1 mt-1.5">
                        <span className="text-[8px] font-mono uppercase tracking-wider text-[var(--accent-blue)]/60">
                          {widget.category}
                        </span>
                        <span className="text-[8px] font-mono text-[var(--text-muted)]">
                          {widget.defaultWidth}x{widget.defaultHeight}
                        </span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

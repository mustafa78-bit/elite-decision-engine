import { useState, useCallback } from "react";
import { AnimatePresence } from "framer-motion";
import { Button } from "../ui/button";
import { DockableWidget } from "./dockable-widget";
import { useWorkspaceStore } from "../../stores/workspace-store";

interface FloatingWidget {
  id: string;
  title: string;
  content: React.ReactNode;
}

export function WorkspaceManager() {
  const [widgets, setWidgets] = useState<FloatingWidget[]>([]);
  const { addPanel } = useWorkspaceStore();

  const addWidget = useCallback((widget: FloatingWidget) => {
    setWidgets((prev) => {
      const updated = [...prev, widget];
      addPanel({
        id: widget.id,
        type: widget.title,
        title: widget.title,
        x: 100 + prev.length * 30,
        y: 100 + prev.length * 30,
        w: 400,
        h: 300,
        minimized: false,
      });
      return updated;
    });
  }, [addPanel]);

  const removeWidget = useCallback((id: string) => {
    setWidgets((prev) => prev.filter((w) => w.id !== id));
  }, []);

  return (
    <>
      <div className="flex gap-2">
        <Button
          variant="glass"
          size="sm"
          onClick={() =>
            addWidget({
              id: `widget-${Date.now()}`,
              title: "Chart",
              content: <div className="text-xs text-[var(--text-secondary)]">Chart widget content</div>,
            })
          }
        >
          + Chart
        </Button>
        <Button
          variant="glass"
          size="sm"
          onClick={() =>
            addWidget({
              id: `widget-${Date.now()}`,
              title: "Signals",
              content: <div className="text-xs text-[var(--text-secondary)]">Signal feed widget content</div>,
            })
          }
        >
          + Signals
        </Button>
        <Button
          variant="glass"
          size="sm"
          onClick={() =>
            addWidget({
              id: `widget-${Date.now()}`,
              title: "Portfolio",
              content: <div className="text-xs text-[var(--text-secondary)]">Portfolio widget content</div>,
            })
          }
        >
          + Portfolio
        </Button>
      </div>

      <AnimatePresence>
        {widgets.map((w) => (
          <DockableWidget
            key={w.id}
            id={w.id}
            title={w.title}
            onClose={removeWidget}
          >
            {w.content}
          </DockableWidget>
        ))}
      </AnimatePresence>
    </>
  );
}

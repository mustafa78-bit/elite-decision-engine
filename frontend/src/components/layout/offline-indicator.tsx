import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

export function OfflineIndicator() {
  const [online, setOnline] = useState(navigator.onLine);

  useEffect(() => {
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }, []);

  return (
    <AnimatePresence>
      {!online && (
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -30 }}
          className="fixed top-0 left-0 right-0 z-[200] flex items-center justify-center gap-2 bg-red-950/90 backdrop-blur-md border-b border-red-800/40 py-1.5"
        >
          <span className="w-2 h-2 rounded-full bg-[var(--accent-red)] animate-pulse" />
          <span className="text-[10px] font-mono text-[var(--accent-red)]">
            No internet connection — data may be stale
          </span>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

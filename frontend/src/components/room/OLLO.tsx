import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { RoomDefinition } from "../../types/room";

interface Props {
  room: RoomDefinition;
  isDoorOpen: boolean;
}

function usePrevious<T>(value: T): T | undefined {
  const [prev, setPrev] = useState<T | undefined>(undefined);
  useEffect(() => {
    setPrev(value);
  }, [value]);
  return prev;
}

export default function OLLO({ room, isDoorOpen }: Props) {
  const [showMessage, setShowMessage] = useState(false);
  const prevRoomId = usePrevious(room.id);
  const isNewRoom = prevRoomId !== undefined && prevRoomId !== room.id;

  const showWelcome = isNewRoom && !isDoorOpen;

  useEffect(() => {
    if (isDoorOpen) {
      setShowMessage(false);
      return;
    }

    const t = setTimeout(() => setShowMessage(true), showWelcome ? 600 : 0);
    return () => clearTimeout(t);
  }, [room.id, isDoorOpen, showWelcome]);

  const message = showWelcome ? room.olloWelcome : room.olloMessage;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex items-end gap-3">
      <AnimatePresence mode="wait">
        {showMessage && (
          <motion.div
            key={`${room.id}-${showWelcome ? 'welcome' : 'msg'}`}
            initial={showWelcome ? { opacity: 0, y: 16, scale: 0.92 } : { opacity: 0, y: 8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.95 }}
            transition={{ duration: 0.5, ease: [0.25, 0.1, 0.25, 1] }}
            className="max-w-[240px]"
          >
            <div
              className="relative px-4 py-2.5 rounded-xl text-[11px] leading-relaxed font-mono tracking-tight"
              style={{
                backgroundColor: `${room.accentDim}dd`,
                border: `1px solid ${room.accent}44`,
                color: room.accent,
                backdropFilter: "blur(12px)",
                boxShadow: `0 4px 24px ${room.accent}22`,
              }}
            >
              {showWelcome && (
                <div className="text-[9px] uppercase tracking-[0.15em] mb-1.5" style={{ opacity: 0.5 }}>
                  OLLO Guide
                </div>
              )}
              {message}
              <div
                className="absolute bottom-0 right-[-6px] w-3 h-3 rotate-45 rounded-sm"
                style={{
                  backgroundColor: `${room.accentDim}dd`,
                  borderRight: `1px solid ${room.accent}44`,
                  borderTop: `1px solid ${room.accent}44`,
                }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        animate={{
          scale: [1, 1.05, 1],
          opacity: [0.8, 1, 0.8],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        className="relative shrink-0 cursor-default select-none"
      >
        <div
          className="w-11 h-11 rounded-full flex items-center justify-center text-lg font-bold"
          style={{
            backgroundColor: `${room.accent}18`,
            border: `1px solid ${room.accent}55`,
            boxShadow: `0 0 24px ${room.accent}33, inset 0 0 24px ${room.accent}18`,
            color: room.accent,
          }}
          title="OLLO — AI Guide"
        >
          <span style={{ filter: `drop-shadow(0 0 6px ${room.accent})` }}>
            ◉
          </span>
        </div>
        <span
          className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full"
          style={{
            backgroundColor: room.accent,
            animation: 'ollo-ping 2.5s ease-in-out infinite',
          }}
        />
      </motion.div>

      <style>{`
        @keyframes ollo-ping {
          0%, 100% { transform: scale(1); opacity: 0.6; box-shadow: 0 0 4px ${room.accent}; }
          50% { transform: scale(1.6); opacity: 0; box-shadow: 0 0 16px ${room.accent}; }
        }
      `}</style>
    </div>
  );
}

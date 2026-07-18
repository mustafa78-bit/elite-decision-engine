import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { RoomDefinition } from "../../types/room";

interface Props {
  room: RoomDefinition;
  prevRoom: RoomDefinition | null;
  onComplete: () => void;
}

export default function RoomDoor({ room, prevRoom, onComplete }: Props) {
  const [phase, setPhase] = useState<'entering' | 'open' | 'exiting' | 'done'>('entering');

  useEffect(() => {
    if (!prevRoom || prevRoom.id === room.id) {
      setPhase('done');
      onComplete();
      return;
    }

    setPhase('entering');
    const t1 = setTimeout(() => setPhase('open'), 280);
    const t2 = setTimeout(() => setPhase('exiting'), 550);
    const t3 = setTimeout(() => {
      setPhase('done');
      onComplete();
    }, 750);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, [room.id, prevRoom, onComplete]);

  if (phase === 'done') return null;

  const isPrevSameAccent = prevRoom && prevRoom.accent === room.accent;

  return (
    <AnimatePresence>
      <motion.div
        key={room.id}
        className="fixed inset-0 z-[100] flex items-center justify-center"
        initial={false}
        animate={{ backgroundColor: 'rgba(7, 11, 20, 0.92)' }}
        exit={{ backgroundColor: 'rgba(7, 11, 20, 0)' }}
        transition={{ duration: 0.35, ease: 'easeInOut' }}
      >
        <div className="relative text-center">
          {/* Door panel slide */}
          <motion.div
            initial={false}
            animate={
              phase === 'entering'
                ? { scale: 0.88, opacity: 0, y: 20 }
                : phase === 'open'
                ? { scale: 1, opacity: 1, y: 0 }
                : { scale: 1.04, opacity: 0, y: -12 }
            }
            transition={{ duration: 0.28, ease: [0.25, 0.1, 0.25, 1] }}
          >
            {/* Classified header */}
            <div
              className="text-[9px] font-mono uppercase tracking-[0.3em] mb-4"
              style={{ color: room.accent, opacity: 0.5 }}
            >
              Accessing Classified Sector
            </div>

            {/* Room name with glow */}
            <motion.div
              animate={{
                textShadow: phase === 'open'
                  ? `0 0 30px ${room.accent}44, 0 0 60px ${room.accent}22`
                  : `0 0 0px transparent`,
              }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            >
              <div
                className="text-4xl font-bold mb-2 tracking-tight"
                style={{ color: room.accent }}
              >
                {room.name}
              </div>
            </motion.div>

            {/* Subtitle */}
            <div
              className="text-sm font-mono tracking-wide"
              style={{ color: room.accent, opacity: 0.5 }}
            >
              {room.subtitle}
            </div>

            {/* Previous room context (if different accent) */}
            {!isPrevSameAccent && prevRoom && (
              <motion.div
                className="mt-6 flex items-center justify-center gap-3"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: phase === 'open' ? 0.4 : 0, y: phase === 'open' ? 0 : -4 }}
                transition={{ duration: 0.3, delay: 0.1 }}
              >
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: prevRoom.accent }}
                />
                <span
                  className="text-[10px] font-mono"
                  style={{ color: prevRoom.accent }}
                >
                  {prevRoom.name}
                </span>
                <span className="text-[var(--text-muted)] text-xs">→</span>
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: room.accent }}
                />
                <span
                  className="text-[10px] font-mono"
                  style={{ color: room.accent }}
                >
                  {room.name}
                </span>
              </motion.div>
            )}
          </motion.div>

          {/* Accent light sweep */}
          <motion.div
            className="absolute -bottom-14 left-1/2 -translate-x-1/2 h-[2px]"
            style={{ backgroundColor: room.accent, boxShadow: `0 0 20px ${room.accent}, 0 0 40px ${room.accent}66` }}
            initial={{ width: 0, opacity: 0 }}
            animate={
              phase === 'open'
                ? { width: 180, opacity: 0.5 }
                : { width: 0, opacity: 0 }
            }
            transition={{ duration: 0.45, ease: 'easeOut' }}
          />
        </div>

        {/* Corner decorations */}
        <div
          className="absolute top-8 left-8 w-12 h-[1px]"
          style={{ backgroundColor: room.accent, opacity: phase === 'open' ? 0.3 : 0 }}
        />
        <div
          className="absolute top-8 left-8 w-[1px] h-12"
          style={{ backgroundColor: room.accent, opacity: phase === 'open' ? 0.3 : 0 }}
        />
        <div
          className="absolute top-8 right-8 w-12 h-[1px]"
          style={{ backgroundColor: room.accent, opacity: phase === 'open' ? 0.3 : 0 }}
        />
        <div
          className="absolute top-8 right-8 w-[1px] h-12"
          style={{ backgroundColor: room.accent, opacity: phase === 'open' ? 0.3 : 0 }}
        />
        <div
          className="absolute bottom-8 left-8 w-12 h-[1px]"
          style={{ backgroundColor: room.accent, opacity: phase === 'open' ? 0.3 : 0 }}
        />
        <div
          className="absolute bottom-8 left-8 w-[1px] h-12"
          style={{ backgroundColor: room.accent, opacity: phase === 'open' ? 0.3 : 0 }}
        />
        <div
          className="absolute bottom-8 right-8 w-12 h-[1px]"
          style={{ backgroundColor: room.accent, opacity: phase === 'open' ? 0.3 : 0 }}
        />
        <div
          className="absolute bottom-8 right-8 w-[1px] h-12"
          style={{ backgroundColor: room.accent, opacity: phase === 'open' ? 0.3 : 0 }}
        />
      </motion.div>
    </AnimatePresence>
  );
}

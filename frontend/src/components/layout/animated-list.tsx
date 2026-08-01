import { motion, AnimatePresence } from "framer-motion";
import type { ReactNode } from "react";

interface AnimatedListProps {
  items: { id: string; content: ReactNode }[];
  className?: string;
}

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.04 },
  },
};

const item = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0 },
};

export function AnimatedList({ items, className }: AnimatedListProps) {
  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className={className}
    >
      <AnimatePresence mode="popLayout">
        {items.map((i) => (
          <motion.div
            key={i.id}
            variants={item}
            layout
            exit={{ opacity: 0, y: -8 }}
            transition={{ type: "spring", stiffness: 300, damping: 24 }}
          >
            {i.content}
          </motion.div>
        ))}
      </AnimatePresence>
    </motion.div>
  );
}

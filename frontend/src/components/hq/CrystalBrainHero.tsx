import { motion } from "framer-motion"

export default function CrystalBrainHero() {
  return (
    <div className="relative flex flex-col items-center justify-center py-6 w-full max-w-xl select-none overflow-hidden">

      {/* Background radial soft ambient glow */}
      <div
        className="absolute rounded-full filter blur-[80px] opacity-40 pointer-events-none"
        style={{
          width: 320,
          height: 320,
          background: "radial-gradient(circle, rgba(79, 140, 255, 0.4) 0%, rgba(139, 92, 246, 0.2) 60%, transparent 100%)",
        }}
      />

      {/* Holographic glowing/expanding energy ripple rings underneath */}
      <div className="absolute w-full h-full flex items-center justify-center pointer-events-none">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="absolute rounded-full border border-[var(--accent-blue)]/20"
            style={{
              width: 140,
              height: 140,
              background: "radial-gradient(circle, transparent 70%, rgba(79, 140, 255, 0.05) 100%)",
              boxShadow: "0 0 16px rgba(79, 140, 255, 0.08), inset 0 0 16px rgba(79, 140, 255, 0.08)",
            }}
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{
              scale: [0.8, 2.2],
              opacity: [0, 0.65, 0],
            }}
            transition={{
              duration: 8,
              repeat: Infinity,
              delay: i * 2.6,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>

      {/* Volumetric Crystal Brain Core Frame */}
      <motion.div
        className="relative z-10 flex items-center justify-center cursor-pointer"
        animate={{
          y: [-6, 6, -6],
          rotate: [-1, 1, -1],
        }}
        transition={{
          duration: 7,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      >
        {/* Crystal Refraction / Chromatic dispersion glows */}
        <div
          className="absolute rounded-full filter blur-[20px] pointer-events-none"
          style={{
            width: 160,
            height: 160,
            background: "linear-gradient(135deg, rgba(255, 93, 115, 0.25) 0%, rgba(79, 140, 255, 0.2) 50%, rgba(139, 92, 246, 0.25) 100%)",
            animation: "ollo-breathe 4s ease-in-out infinite alternate",
          }}
        />

        {/* Outer Glassmorphic boundary ring */}
        <div
          className="absolute rounded-full border border-white/10"
          style={{
            width: 170,
            height: 170,
            background: "radial-gradient(circle at 35% 30%, rgba(255,255,255,0.06) 0%, transparent 70%)",
            boxShadow: "0 10px 30px rgba(0, 0, 0, 0.4), inset 0 2px 8px rgba(255,255,255,0.15)",
            backdropFilter: "blur(8px)",
          }}
        />

        {/* Detailed SVG Organism Crystal Brain */}
        <svg
          width="160"
          height="160"
          viewBox="0 0 200 200"
          className="relative z-20 overflow-visible"
        >
          <defs>
            {/* Soft metallic and neon linear gradients */}
            <linearGradient id="crystalGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#4F8CFF" />
              <stop offset="50%" stopColor="#8B5CF6" />
              <stop offset="100%" stopColor="#3EDC97" />
            </linearGradient>
            <radialGradient id="brainGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#8B5CF6" stopOpacity="0.8" />
              <stop offset="60%" stopColor="#4F8CFF" stopOpacity="0.2" />
              <stop offset="100%" stopColor="transparent" stopOpacity="0" />
            </radialGradient>
            <filter id="neonGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="6" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Central Pulsating Energy Field */}
          <motion.circle
            cx="100"
            cy="100"
            r="45"
            fill="url(#brainGlow)"
            animate={{
              r: [40, 52, 40],
              opacity: [0.7, 0.95, 0.7],
            }}
            transition={{
              duration: 4,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />

          {/* Neural Crystal Lattice Connections / Back Lines */}
          <g stroke="rgba(79, 140, 255, 0.15)" strokeWidth="0.8">
            <line x1="100" y1="50" x2="60" y2="85" />
            <line x1="100" y1="50" x2="140" y2="85" />
            <line x1="60" y1="85" x2="70" y2="135" />
            <line x1="140" y1="85" x2="130" y2="135" />
            <line x1="70" y1="135" x2="100" y2="165" />
            <line x1="130" y1="135" x2="100" y2="165" />

            {/* Inner web lines */}
            <line x1="100" y1="50" x2="100" y2="105" />
            <line x1="60" y1="85" x2="100" y2="105" />
            <line x1="140" y1="85" x2="100" y2="105" />
            <line x1="70" y1="135" x2="100" y2="105" />
            <line x1="130" y1="135" x2="100" y2="105" />

            {/* Asymmetrical crystal nodes connection */}
            <line x1="60" y1="85" x2="75" y2="60" />
            <line x1="100" y1="50" x2="75" y2="60" />
            <line x1="140" y1="85" x2="125" y2="60" />
            <line x1="100" y1="50" x2="125" y2="60" />
          </g>

          {/* Glowing Crystal Brain Nodes (Neural Hemispheres) */}
          <g filter="url(#neonGlow)">
            {/* Frontal Cortex Area */}
            <motion.circle
              cx="100"
              cy="50"
              r="6.5"
              fill="url(#crystalGrad)"
              animate={{ fill: ["#4F8CFF", "#8B5CF6", "#4F8CFF"] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            />
            <motion.circle
              cx="75"
              cy="60"
              r="4.5"
              fill="#4F8CFF"
              animate={{ opacity: [0.6, 1, 0.6] }}
              transition={{ duration: 3.5, repeat: Infinity, ease: "easeInOut" }}
            />
            <motion.circle
              cx="125"
              cy="60"
              r="4.5"
              fill="#8B5CF6"
              animate={{ opacity: [1, 0.5, 1] }}
              transition={{ duration: 3.2, repeat: Infinity, ease: "easeInOut" }}
            />

            {/* Temporal Lobe Regions (Left and Right) */}
            <motion.circle
              cx="60"
              cy="85"
              r="7"
              fill="url(#crystalGrad)"
              animate={{ fill: ["#8B5CF6", "#3EDC97", "#8B5CF6"] }}
              transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut" }}
            />
            <motion.circle
              cx="140"
              cy="85"
              r="7"
              fill="url(#crystalGrad)"
              animate={{ fill: ["#3EDC97", "#4F8CFF", "#3EDC97"] }}
              transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
            />

            {/* Central Decisive Core */}
            <motion.circle
              cx="100"
              cy="105"
              r="9"
              fill="#FFFFFF"
              style={{ filter: "drop-shadow(0 0 8px rgba(255,255,255,0.8))" }}
              animate={{
                scale: [0.95, 1.15, 0.95],
              }}
              transition={{
                duration: 2.5,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />

            {/* Occipital / Hippocampus Regions (Sensing & Memory base) */}
            <motion.circle
              cx="70"
              cy="135"
              r="5.5"
              fill="#3EDC97"
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 2.8, repeat: Infinity, ease: "easeInOut" }}
            />
            <motion.circle
              cx="130"
              cy="135"
              r="5.5"
              fill="#4F8CFF"
              animate={{ opacity: [1, 0.4, 1] }}
              transition={{ duration: 3.6, repeat: Infinity, ease: "easeInOut" }}
            />
            <motion.circle
              cx="100"
              cy="165"
              r="6"
              fill="url(#crystalGrad)"
              animate={{ fill: ["#4F8CFF", "#3EDC97", "#4F8CFF"] }}
              transition={{ duration: 4.8, repeat: Infinity, ease: "easeInOut" }}
            />
          </g>

          {/* Dynamic Floating Active Signal Streams (Neural Transmissions) */}
          {[
            { delay: 0, path: "M 100,50 L 60,85 L 100,105" },
            { delay: 1.5, path: "M 100,50 L 140,85 L 100,105" },
            { delay: 3, path: "M 100,165 L 70,135 L 100,105" },
            { delay: 4.5, path: "M 100,165 L 130,135 L 100,105" },
          ].map((stream, idx) => (
            <path
              key={idx}
              d={stream.path}
              fill="none"
              stroke="rgba(255, 255, 255, 0.65)"
              strokeWidth="1.2"
              strokeDasharray="6 30"
              style={{
                animation: `neural-stream 3.5s linear infinite`,
                animationDelay: `${stream.delay}s`,
              }}
            />
          ))}
        </svg>

        {/* Volumetric Holographic dust particles drifting */}
        <div className="absolute w-full h-full pointer-events-none">
          {[0, 1, 2, 3, 4].map((i) => (
            <motion.span
              key={i}
              className="absolute w-1 h-1 rounded-full bg-white/40"
              style={{
                top: `${20 + i * 15}%`,
                left: `${15 + i * 18}%`,
              }}
              animate={{
                y: [0, -30, 0],
                x: [0, 15, 0],
                opacity: [0, 0.75, 0],
                scale: [0.5, 1.2, 0.5],
              }}
              transition={{
                duration: 5 + i,
                repeat: Infinity,
                delay: i * 0.8,
                ease: "easeInOut",
              }}
            />
          ))}
        </div>
      </motion.div>

      {/* Styled custom animations */}
      <style>{`
        @keyframes neural-stream {
          to {
            stroke-dashoffset: -36;
          }
        }
      `}</style>
    </div>
  )
}

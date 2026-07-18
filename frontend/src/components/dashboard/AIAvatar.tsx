import { useState, useEffect } from "react";

interface Props {
  size?: number;
  pulse?: boolean;
}

function useMounted() {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  return mounted;
}

export default function AIAvatar({ size = 40, pulse = true }: Props) {
  const mounted = useMounted();

  return (
    <div
      style={{
        width: size,
        height: size,
        position: "relative",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        opacity: mounted ? 1 : 0,
        transition: "opacity 0.6s ease-out",
      }}
    >
      {/* Outer rotating ring */}
      <div
        style={{
          position: "absolute",
          inset: -4,
          borderRadius: "50%",
          background: "conic-gradient(from 0deg, rgba(139,92,246,0.4), rgba(139,92,246,0.05), rgba(139,92,246,0.4), rgba(139,92,246,0.05), rgba(139,92,246,0.4))",
          animation: "rotate 8s linear infinite",
          mask: "radial-gradient(farthest-side, transparent calc(100% - 1.5px), #000 calc(100% - 1.5px))",
          WebkitMask: "radial-gradient(farthest-side, transparent calc(100% - 1.5px), #000 calc(100% - 1.5px))",
        }}
      />

      {/* Glow / breathing layer */}
      <div
        style={{
          position: "absolute",
          width: size * 0.75,
          height: size * 0.75,
          borderRadius: "50%",
          background: "rgba(139, 92, 246, 0.15)",
          filter: "blur(8px)",
          animation: pulse ? "breathe 3s ease-in-out infinite" : "none",
        }}
      />

      {/* Core */}
      <div
        style={{
          width: size * 0.35,
          height: size * 0.35,
          borderRadius: "50%",
          background: "radial-gradient(circle at 35% 35%, #A78BFA, #7C3AED)",
          boxShadow: "0 0 12px rgba(139,92,246,0.3)",
          position: "relative",
          zIndex: 1,
        }}
      />
    </div>
  );
}
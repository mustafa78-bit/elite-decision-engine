import { useEffect, useState, useRef } from "react";
import type { RoomDefinition } from "../../types/room";

interface Dot {
  id: number;
  x: number;
  y: number;
  size: number;
  delay: number;
  duration: number;
  driftX: number;
  driftY: number;
  dir: number;
}

interface Props {
  room: RoomDefinition;
}

function hashSeed(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) - h) + s.charCodeAt(i);
    h |= 0;
  }
  return h;
}

function pseudoRandom(seed: number): () => number {
  let s = seed;
  return () => {
    s = (s * 16807 + 1) % 2147483647;
    return (s % 1000) / 1000;
  };
}

function generateDots(room: RoomDefinition): Dot[] {
  const p = room.particles;
  const rng = pseudoRandom(hashSeed(room.id));
  const isHorizontal = p.behavior === 'scan';
  const isVertical = p.behavior === 'rise';
  const spreadX = isHorizontal ? 120 : p.driftX;
  const spreadY = isVertical ? 120 : p.driftY;

  const dots: Dot[] = [];
  for (let i = 0; i < p.density; i++) {
    const x = rng() * 100;
    const y = rng() * 100;
    const size = p.minSize + rng() * (p.maxSize - p.minSize);
    const delay = rng() * p.speed;
    const duration = p.speed * (0.8 + rng() * 0.6);
    const dir = rng() > 0.5 ? 1 : -1;

    let driftX: number, driftY: number;

    switch (p.behavior) {
      case 'scan':
        driftX = spreadX * dir;
        driftY = (rng() - 0.5) * 10;
        break;
      case 'rise':
        driftX = (rng() - 0.5) * 10;
        driftY = -spreadY * rng();
        break;
      case 'flow':
        driftX = spreadX * dir * rng();
        driftY = (rng() - 0.5) * 15;
        break;
      case 'ember':
        driftX = (rng() - 0.5) * spreadX;
        driftY = -spreadY * rng() * 0.5;
        break;
      case 'grid':
        driftX = (rng() - 0.5) * spreadX * 0.5;
        driftY = (rng() - 0.5) * spreadY * 0.5;
        break;
      default:
        driftX = (rng() - 0.5) * spreadX;
        driftY = (rng() - 0.5) * spreadY;
    }

    dots.push({ id: i, x, y, size, delay, duration, driftX, driftY, dir });
  }
  return dots;
}

function getKeyframes(behavior: string): string {
  switch (behavior) {
    case 'scan':
      return `0%, 100% { transform: translateX(0); opacity: 0; }
              5% { opacity: 0.6; }
              50% { transform: translateX(var(--drift-x)); opacity: 0.1; }
              95% { opacity: 0.6; }`;
    case 'rise':
      return `0%, 100% { transform: translateY(0); opacity: 0; }
              10% { opacity: 0.5; }
              50% { transform: translateY(var(--drift-y)); opacity: 0.1; }
              90% { opacity: 0.4; }`;
    case 'flow':
      return `0%, 100% { transform: translate(0, 0); opacity: 0; }
              10% { opacity: 0.5; }
              45% { transform: translate(calc(var(--drift-x) * 0.7), calc(var(--drift-y) * 0.7)); opacity: 0.15; }
              55% { transform: translate(var(--drift-x), var(--drift-y)); opacity: 0.15; }
              90% { opacity: 0.4; }`;
    case 'ember':
      return `0%, 100% { transform: translate(0, 0) scale(1); opacity: 0; }
              10% { opacity: 0.6; transform: translate(calc(var(--drift-x) * 0.3), calc(var(--drift-y) * 0.3)) scale(1.2); }
              50% { transform: translate(var(--drift-x), var(--drift-y)) scale(0.6); opacity: 0.2; }
              90% { opacity: 0.5; }`;
    case 'grid':
      return `0%, 100% { transform: translate(0, 0); opacity: 0; }
              10% { opacity: 0.4; }
              50% { transform: translate(var(--drift-x), var(--drift-y)); opacity: 0.1; }
              90% { opacity: 0.3; }`;
    default:
      return `0%, 100% { transform: translate(0, 0); opacity: 0; }
              10% { opacity: 0.5; }
              50% { transform: translate(var(--drift-x), var(--drift-y)); opacity: 0.12; }
              90% { opacity: 0.4; }`;
  }
}

export default function Particles({ room }: Props) {
  const [dots, setDots] = useState<Dot[]>(() => generateDots(room));
  const prevId = useRef(room.id);

  useEffect(() => {
    if (prevId.current !== room.id) {
      setDots(generateDots(room));
      prevId.current = room.id;
    }
  }, [room]);

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
      <style>{`
        @keyframes particle-behavior { ${getKeyframes(room.particles.behavior)} }
      `}</style>
      {dots.map((dot) => (
        <div
          key={dot.id}
          className="absolute rounded-full"
          style={{
            left: `${dot.x}%`,
            top: `${dot.y}%`,
            width: dot.size,
            height: dot.size,
            backgroundColor: room.accent,
            boxShadow: `0 0 ${dot.size * 3}px ${room.accent}66`,
            '--drift-x': `${dot.driftX}px`,
            '--drift-y': `${dot.driftY}px`,
            animation: `particle-behavior ${dot.duration}s ${dot.delay}s infinite ease-in-out`,
            willChange: 'transform, opacity',
          } as React.CSSProperties}
        />
      ))}
    </div>
  );
}

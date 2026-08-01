import { useRef, useState, useMemo, useEffect, useCallback, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { getRoomForPath, type RoomDefinition } from "../../types/room";
import Particles from "./Particles";
import OLLO from "./OLLO";
import RoomDoor from "./RoomDoor";

interface Props {
  children: ReactNode;
}

export default function Room({ children }: Props) {
  const { pathname } = useLocation();

  const room = useMemo(() => getRoomForPath(pathname), [pathname]);
  const prevRoomRef = useRef<RoomDefinition>(room);

  const [doorQueue, setDoorQueue] = useState<{ room: RoomDefinition; prev: RoomDefinition } | null>(null);
  const [isDoorOpen, setIsDoorOpen] = useState(false);

  const isNewRoom = prevRoomRef.current.id !== room.id;

  useEffect(() => {
    if (isNewRoom) {
      setDoorQueue({ room, prev: prevRoomRef.current });
      setIsDoorOpen(true);
      prevRoomRef.current = room;
    }
  }, [room, isNewRoom]);

  const handleDoorComplete = useCallback(() => {
    setDoorQueue(null);
    setIsDoorOpen(false);
  }, []);

  const roomStyle = {
    '--room-accent': room.accent,
    '--room-accent-dim': room.accentDim,
    '--room-accent-glow': room.accentGlow,
    '--room-gradient': room.gradient,
    '--room-ambient': room.lighting.ambientColor,
    '--room-ambient-intensity': room.lighting.ambientIntensity,
    '--room-vignette': room.lighting.vignetteColor,
    '--room-vignette-opacity': room.lighting.vignetteOpacity,
    '--room-scanline-opacity': room.lighting.scanlineOpacity,
  } as React.CSSProperties;

  return (
    <>
      {doorQueue && (
        <RoomDoor
          room={doorQueue.room}
          prevRoom={doorQueue.prev}
          onComplete={handleDoorComplete}
        />
      )}
      <div className="relative min-h-full room-shell" style={roomStyle}>
        {/* Ambient gradient background */}
        <div
          className="absolute inset-0 transition-opacity duration-1000"
          style={{ background: room.gradient, opacity: 0.6 }}
          aria-hidden="true"
        />
        {/* Ambient color wash */}
        <div
          className="absolute inset-0 transition-opacity duration-700 pointer-events-none"
          style={{
            backgroundColor: room.lighting.ambientColor,
            opacity: room.lighting.ambientIntensity,
          }}
          aria-hidden="true"
        />
        {/* Vignette overlay */}
        <div
          className="absolute inset-0 pointer-events-none transition-opacity duration-700"
          style={{
            background: `radial-gradient(ellipse at center, transparent 50%, ${room.lighting.vignetteColor} 100%)`,
            opacity: room.lighting.vignetteOpacity,
          }}
          aria-hidden="true"
        />
        {/* Scanline overlay */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage: `repeating-linear-gradient(0deg, transparent, transparent 1px, rgba(255,255,255,0.03) 1px, rgba(255,255,255,0.03) 2px)`,
            opacity: room.lighting.scanlineOpacity,
            backgroundSize: '100% 2px',
          }}
          aria-hidden="true"
        />
        <Particles room={room} />
        <div className="relative z-10">
          {children}
        </div>
        <OLLO room={room} isDoorOpen={isDoorOpen} />
      </div>
    </>
  );
}

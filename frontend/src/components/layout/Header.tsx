import type { ConnectionStatus, WsRoomStatus } from "../../types/connection";
import { ConnectionStatusBadge } from "./ConnectionStatus";

interface Props {
  status: ConnectionStatus;
  wsRooms: WsRoomStatus;
}

export default function Header({ wsRooms }: Props) {
  return (
    <header className="flex items-center justify-between border-b border-gray-800 px-4 py-2">
      <div>
        <h1 className="text-sm font-semibold tracking-wide text-gray-100">
          Elite Terminal
        </h1>
        <p className="text-[9px] text-gray-600 uppercase tracking-widest">
          Decision Engine v1
        </p>
      </div>
      <div className="flex items-center gap-3">
        <div className="flex gap-1.5">
          {Object.entries(wsRooms).map(([room, s]) => (
            <span
              key={room}
              className={`inline-block w-1.5 h-1.5 rounded-full ${s === "CONNECTED" ? "bg-green-500" : "bg-red-500"}`}
              title={`${room}: ${s}`}
            />
          ))}
        </div>
        <ConnectionStatusBadge wsRooms={wsRooms as unknown as Record<string, ConnectionStatus>} />
      </div>
    </header>
  );
}

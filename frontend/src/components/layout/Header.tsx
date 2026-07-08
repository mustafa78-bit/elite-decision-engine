import type { ConnectionStatus } from "../../websocket/client.ts";

interface Props {
  status: ConnectionStatus;
}

export default function Header({ status }: Props) {
  const color = status === "CONNECTED" ? "bg-green-500" : "bg-red-500";
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
      <div className="flex items-center gap-2">
        <span className={`inline-block w-1.5 h-1.5 rounded-full ${color}`} />
        <span className="text-[9px] text-gray-600 uppercase">{status}</span>
      </div>
    </header>
  );
}

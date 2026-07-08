interface Props {
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export default function CandleStatus({ open, high, low, close, volume }: Props) {
  const isGreen = close >= open;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-2">
        Latest Candle
      </h3>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        <div>
          <span className="text-gray-500">Open</span>
          <span className="float-right tabular-nums text-gray-300">${open.toFixed(2)}</span>
        </div>
        <div>
          <span className="text-gray-500">Close</span>
          <span className={`float-right tabular-nums ${isGreen ? "text-green-400" : "text-red-400"}`}>
            ${close.toFixed(2)}
          </span>
        </div>
        <div>
          <span className="text-gray-500">High</span>
          <span className="float-right tabular-nums text-gray-300">${high.toFixed(2)}</span>
        </div>
        <div>
          <span className="text-gray-500">Low</span>
          <span className="float-right tabular-nums text-gray-300">${low.toFixed(2)}</span>
        </div>
        <div className="col-span-2">
          <span className="text-gray-500">Volume</span>
          <span className="float-right tabular-nums text-gray-300">
            {volume >= 1_000_000
              ? `${(volume / 1_000_000).toFixed(2)}M`
              : volume.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
}

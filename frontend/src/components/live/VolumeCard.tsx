interface Props {
  volume24h: number;
  symbol?: string;
}

export default function VolumeCard({ volume24h, symbol = "BTC" }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-2">
        {symbol} Volume (24h)
      </h3>
      <div className="text-lg font-bold tabular-nums text-[var(--text-primary)]">
        {volume24h >= 1_000_000
          ? `${(volume24h / 1_000_000).toFixed(2)}M`
          : volume24h >= 1_000
            ? `${(volume24h / 1_000).toFixed(2)}K`
            : volume24h.toFixed(2)}
      </div>
    </div>
  );
}

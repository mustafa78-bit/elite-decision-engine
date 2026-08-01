import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface OrderBookLevel {
  price: number;
  size: number;
  total: number;
}

interface OrderBookProps {
  symbol?: string;
  bids?: OrderBookLevel[];
  asks?: OrderBookLevel[];
  maxTotal?: number;
}

export function OrderBook({
  symbol = "BTC/USDT",
  bids = [
    { price: 42850, size: 12.5, total: 535625 },
    { price: 42800, size: 8.3, total: 355240 },
    { price: 42750, size: 15.1, total: 645525 },
    { price: 42700, size: 6.7, total: 286090 },
    { price: 42650, size: 10.2, total: 435030 },
    { price: 42600, size: 4.5, total: 191700 },
    { price: 42550, size: 9.8, total: 416990 },
    { price: 42500, size: 3.2, total: 136000 },
    { price: 42450, size: 7.6, total: 322620 },
    { price: 42400, size: 5.4, total: 228960 },
  ],
  asks = [
    { price: 42900, size: 11.2, total: 480480 },
    { price: 42950, size: 6.8, total: 292060 },
    { price: 43000, size: 14.3, total: 614900 },
    { price: 43050, size: 5.1, total: 219555 },
    { price: 43100, size: 9.6, total: 413760 },
    { price: 43150, size: 7.2, total: 310680 },
    { price: 43200, size: 3.8, total: 164160 },
    { price: 43250, size: 8.9, total: 384925 },
    { price: 43300, size: 4.1, total: 177530 },
    { price: 43350, size: 6.3, total: 273105 },
  ],
}: OrderBookProps) {
  const maxBidTotal = Math.max(...bids.map((b) => b.total), 1);
  const maxAskTotal = Math.max(...asks.map((a) => a.total), 1);

  const spread = asks[0]?.price - bids[0]?.price;
  const spreadPct = (spread / asks[0]?.price) * 100;

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Order Book</CardTitle>
          <span className="text-[9px] font-mono text-[var(--text-muted)]">
            Spread: ${spread.toFixed(1)} ({spreadPct.toFixed(3)}%)
          </span>
        </div>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">{symbol}</span>
      </CardHeader>
      <CardContent className="p-0">
        <div className="px-3 py-1 border-b border-[var(--border-subtle)] flex text-[8px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
          <span className="flex-[2]">Price</span>
          <span className="flex-[1] text-right">Size</span>
          <span className="flex-[2] text-right">Total</span>
        </div>
        <div className="max-h-48 overflow-y-auto">
          {asks.reverse().map((a) => (
            <div key={a.price} className="relative flex items-center px-3 py-0.5 text-[10px] font-mono hover:bg-[var(--bg-hover)]">
              <div
                className="absolute right-0 top-0 bottom-0 bg-[var(--accent-red)]/10"
                style={{ width: `${(a.total / maxAskTotal) * 100}%` }}
              />
              <span className="flex-[2] text-[var(--accent-red)] tabular-nums">{a.price.toFixed(1)}</span>
              <span className="flex-[1] text-right text-[var(--text-secondary)] tabular-nums">{a.size.toFixed(2)}</span>
              <span className="flex-[2] text-right text-[var(--text-muted)] tabular-nums">{(a.total / 1000).toFixed(0)}K</span>
            </div>
          ))}
        </div>
        <div className="px-3 py-1 border-y border-[var(--border-subtle)] bg-[var(--bg-base)] text-center text-[10px] font-mono font-medium text-[var(--text-primary)] tabular-nums">
          {bids[0]?.price.toFixed(1)} — {asks[0]?.price.toFixed(1)}
        </div>
        <div className="max-h-48 overflow-y-auto">
          {bids.map((b) => (
            <div key={b.price} className="relative flex items-center px-3 py-0.5 text-[10px] font-mono hover:bg-[var(--bg-hover)]">
              <div
                className="absolute right-0 top-0 bottom-0 bg-[var(--accent-green)]/10"
                style={{ width: `${(b.total / maxBidTotal) * 100}%` }}
              />
              <span className="flex-[2] text-[var(--accent-green)] tabular-nums">{b.price.toFixed(1)}</span>
              <span className="flex-[1] text-right text-[var(--text-secondary)] tabular-nums">{b.size.toFixed(2)}</span>
              <span className="flex-[2] text-right text-[var(--text-muted)] tabular-nums">{(b.total / 1000).toFixed(0)}K</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

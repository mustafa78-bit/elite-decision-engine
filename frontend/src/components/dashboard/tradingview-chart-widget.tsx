import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "../ui/card";

interface ChartCandle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

const mockCandles: ChartCandle[] = [
  { time: "09:00", open: 96200, high: 96800, low: 96100, close: 96700, volume: 15.4 },
  { time: "10:00", open: 96700, high: 97100, low: 96500, close: 96900, volume: 22.1 },
  { time: "11:00", open: 96900, high: 97500, low: 96700, close: 97400, volume: 29.8 },
  { time: "12:00", open: 97400, high: 97800, low: 97200, close: 97550, volume: 18.5 },
  { time: "13:00", open: 97550, high: 97600, low: 96900, close: 97200, volume: 34.2 },
  { time: "14:00", open: 97200, high: 97650, low: 97100, close: 97450, volume: 19.9 },
  { time: "15:00", open: 97450, high: 98100, low: 97300, close: 97900, volume: 44.5 },
  { time: "16:00", open: 97900, high: 98400, low: 97700, close: 98250, volume: 38.1 },
];

export function TradingViewChartWidget() {
  const navigate = useNavigate();
  const [selectedOverlay, setSelectedOverlay] = useState<"EMA20" | "EMA50" | "RSI">("EMA20");
  const [candles] = useState<ChartCandle[]>(mockCandles);

  // Simple math to convert price values to SVG coordinates
  const prices = candles.flatMap((c) => [c.high, c.low]);
  const minPrice = Math.min(...prices) * 0.998;
  const maxPrice = Math.max(...prices) * 1.002;
  const priceRange = maxPrice - minPrice;

  const width = 340;
  const height = 140;

  const getX = (index: number) => {
    return (index / (candles.length - 1)) * (width - 40) + 15;
  };

  const getY = (price: number) => {
    return height - ((price - minPrice) / priceRange) * (height - 30) - 15;
  };

  return (
    <Card
      className="h-full border-[var(--border-default)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all flex flex-col justify-between"
      role="region"
      aria-label="TradingView Chart Engine"
    >
      <CardContent className="p-2.5 flex flex-col h-full justify-between gap-1.5">
        <div>
          {/* Header controls */}
          <div className="flex items-center justify-between mb-1.5 pb-1 border-b border-[var(--border-subtle)]">
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">TradingView Core</span>
              <div className="flex gap-1">
                {["EMA20", "EMA50", "RSI"].map((o) => (
                  <button
                    key={o}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedOverlay(o as any);
                    }}
                    className={`px-1 py-0 rounded text-[8px] font-mono transition-all ${
                      selectedOverlay === o
                        ? "bg-[var(--accent-blue)]/25 text-[var(--accent-blue)] border border-[var(--accent-blue)]/30"
                        : "bg-[var(--bg-elevated)] text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
                    }`}
                  >
                    {o}
                  </button>
                ))}
              </div>
            </div>
            <span className="text-[9px] text-[var(--text-muted)] font-mono cursor-pointer" onClick={() => navigate("/live-market")}>◈ Link</span>
          </div>

          {/* SVG Candlestick Chart Representation */}
          <div
            className="relative bg-black/45 rounded border border-[var(--border-subtle)] overflow-hidden cursor-pointer"
            onClick={() => navigate("/live-market")}
          >
            <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-[142px]">
              {/* Gridlines */}
              {Array.from({ length: 4 }).map((_, i) => {
                const yVal = minPrice + (priceRange / 4) * i;
                const yPos = getY(yVal);
                return (
                  <line
                    key={i}
                    x1="0"
                    y1={yPos}
                    x2={width - 30}
                    y2={yPos}
                    stroke="var(--border-subtle)"
                    strokeWidth="0.5"
                    strokeDasharray="2,2"
                  />
                );
              })}

              {/* Candles */}
              {candles.map((c, i) => {
                const x = getX(i);
                const highY = getY(c.high);
                const lowY = getY(c.low);
                const openY = getY(c.open);
                const closeY = getY(c.close);
                const isBullish = c.close >= c.open;
                const bodyY = Math.min(openY, closeY);
                const bodyHeight = Math.max(Math.abs(openY - closeY), 1.5);
                const candleColor = isBullish ? "var(--accent-green)" : "var(--accent-red)";

                return (
                  <g key={i}>
                    {/* Wick */}
                    <line
                      x1={x}
                      y1={highY}
                      x2={x}
                      y2={lowY}
                      stroke={candleColor}
                      strokeWidth="1.2"
                    />
                    {/* Body */}
                    <rect
                      x={x - 4}
                      y={bodyY}
                      width="8"
                      height={bodyHeight}
                      fill={candleColor}
                      stroke={candleColor}
                      strokeWidth="0.5"
                    />
                  </g>
                );
              })}

              {/* Overlay Indicator lines */}
              {selectedOverlay === "EMA20" && (
                <polyline
                  fill="none"
                  stroke="var(--accent-blue)"
                  strokeWidth="1.5"
                  points={candles.map((c, i) => `${getX(i)},${getY(c.close * 0.9995)}`).join(" ")}
                />
              )}
              {selectedOverlay === "EMA50" && (
                <polyline
                  fill="none"
                  stroke="var(--accent-purple)"
                  strokeWidth="1.5"
                  points={candles.map((c, i) => `${getX(i)},${getY(c.close * 0.998)}`).join(" ")}
                />
              )}
              {selectedOverlay === "RSI" && (
                <polyline
                  fill="none"
                  stroke="var(--accent-yellow)"
                  strokeWidth="1.5"
                  points={candles.map((c, i) => `${getX(i)},${getY((c.close - 95000) * 0.4 + 96000)}`).join(" ")}
                />
              )}

              {/* Right price scale ticks */}
              <text x={width - 28} y={getY(maxPrice * 0.995)} fill="var(--text-muted)" fontSize="8" fontFamily="monospace">
                {Math.round(maxPrice).toLocaleString()}
              </text>
              <text x={width - 28} y={getY(minPrice * 1.005)} fill="var(--text-muted)" fontSize="8" fontFamily="monospace">
                {Math.round(minPrice).toLocaleString()}
              </text>
            </svg>
          </div>
        </div>

        <div className="mt-1 pt-1.5 border-t border-[var(--border-subtle)] flex items-center justify-between text-[9px] font-mono text-[var(--text-muted)]">
          <span>BTC/USDT 1H Candle Interval</span>
          <span className="text-[var(--accent-green)] font-semibold">MACD Golden Cross Confirmed</span>
        </div>
      </CardContent>
    </Card>
  );
}

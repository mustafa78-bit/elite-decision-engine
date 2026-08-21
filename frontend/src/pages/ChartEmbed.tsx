import { useEffect, useState } from "react";
import { apiFetch } from "../api/client";
import { ChartPanel } from "../components/trading/chart-panel";
import { useTerminalStore } from "../stores/terminal-store";
import type { TradePayload } from "../types/trade";

interface LiveCandle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

declare global {
  interface Window {
    __CHART_READY__?: boolean;
  }
}

// Bare, unauthenticated-looking (but token-bearing) page that renders just
// the real ChartPanel -- same component, same overlays (S/R, RSI
// divergence, trend channel, liquidity zones, volume profile) a user sees
// in the app -- for headless-browser screenshotting by
// services/telegram/chart_screenshot.py. Not linked from anywhere in the
// app's own navigation; reached only via a URL the backend builds itself
// with a short-lived token (see notifications/dispatcher.py).
export default function ChartEmbed() {
  const setSymbol = useTerminalStore((s) => s.setSymbol);
  const [ready, setReady] = useState(false);
  const [data, setData] = useState<Candle[]>([]);
  const [openTrades, setOpenTrades] = useState<TradePayload[]>([]);
  const [timeframe, setTimeframe] = useState("1h");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    if (token) localStorage.setItem("auth_token", token);

    const symbol = (params.get("symbol") || "BTC").replace(/USDT$/, "");
    const tf = params.get("timeframe") || "1h";
    const side = params.get("side") || "LONG";
    const entry = Number(params.get("entry"));
    const stop = params.get("stop") ? Number(params.get("stop")) : undefined;
    const tp1 = params.get("tp1") ? Number(params.get("tp1")) : undefined;
    const tp2 = params.get("tp2") ? Number(params.get("tp2")) : undefined;

    setSymbol(symbol);
    setTimeframe(tf);
    setOpenTrades(
      entry
        ? [{ symbol: `${symbol}USDT`, side, entry, stop, tp1, tp2, status: "OPEN" }]
        : []
    );

    apiFetch<{ candles?: LiveCandle[]; error?: string }>(`/market/live?symbol=${symbol}&timeframe=${tf}&limit=150`)
      .then((res) => {
        if (res.candles && res.candles.length > 0) {
          setData(res.candles.map((c) => ({
            time: Math.floor(c.timestamp / 1000),
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
            volume: c.volume,
          })));
        } else {
          // A 200 with no candles (e.g. the collector's own error shape,
          // {"error": "..."}, on an exchange rate-limit) is not a fetch
          // failure apiFetch would throw on -- ChartPanel's onReady never
          // fires when data is empty (its render effect bails out before
          // reaching the overlay fetches), so signal done here or the
          // Python screenshot's wait_for_function would hang until its own
          // timeout with nothing further to actually wait for.
          window.__CHART_READY__ = true;
        }
      })
      .catch(() => {
        setData([]);
        window.__CHART_READY__ = true;
      })
      .finally(() => setReady(true));
  }, [setSymbol]);

  if (!ready) return null;

  return (
    <div
      data-testid="chart-embed-root"
      style={{ width: "1280px", height: "500px", background: "var(--bg-app, #0a0e14)", padding: "16px" }}
    >
      <ChartPanel
        data={data}
        timeframe={timeframe}
        openTrades={openTrades}
        onReady={() => { window.__CHART_READY__ = true; }}
      />
    </div>
  );
}

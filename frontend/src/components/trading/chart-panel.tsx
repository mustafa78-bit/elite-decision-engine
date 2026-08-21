import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { LineWidth } from "lightweight-charts";
import { Maximize2, X } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { useTerminalStore } from "../../stores/terminal-store";
import type { TradePayload } from "../../types/trade";
import type { ScannerOpportunity } from "../../api/scanner";

interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

// Seeded with the first close rather than an initial SMA over `period`
// candles -- simpler, and matches what most lightweight charting libraries
// do by default; the difference washes out after the first ~2x period
// candles anyway.
export function computeEma(closes: number[], period: number): number[] {
  const k = 2 / (period + 1);
  const result: number[] = [];
  let prev: number | null = null;
  for (const close of closes) {
    prev = prev === null ? close : close * k + prev * (1 - k);
    result.push(prev);
  }
  return result;
}

interface ChartPanelProps {
  data?: Candle[];
  timeframe?: string;
  openTrades?: TradePayload[];
  opportunities?: ScannerOpportunity[];
  // Fires once after every overlay fetch (S/R, divergence, channel,
  // liquidity zones, volume profile) has settled and the chart has drawn
  // whatever it got -- used by the embed page (services/telegram's
  // screenshot capture) as a deterministic "safe to screenshot now" signal
  // instead of a fixed timeout.
  onReady?: () => void;
}

// Minimal shape of what this component actually calls on the real
// lightweight-charts chart/series objects -- avoids depending on their
// exact exported type names (which have moved between package versions)
// while still catching real typos at compile time.
interface MinimalSeries {
  setData: (data: any[]) => void;
  createPriceLine: (opts: any) => any;
  removePriceLine: (line: any) => void;
  priceToCoordinate: (price: number) => number | null;
}
interface MinimalChart {
  applyOptions: (opts: { width: number; height: number }) => void;
  timeScale: () => { fitContent: () => void };
  remove: () => void;
}
interface ChartHandles {
  chart: MinimalChart;
  candleSeries: MinimalSeries;
  ema20Series: MinimalSeries;
  ema50Series: MinimalSeries;
  drawVolumeProfile: () => void;
}

export function ChartPanel({ data = [], timeframe = "1h", openTrades = [], opportunities = [], onReady }: ChartPanelProps) {
  const { t } = useTranslation("tradingWorkspace");
  const containerRef = useRef<HTMLDivElement>(null);
  const { symbol } = useTerminalStore();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [handles, setHandles] = useState<ChartHandles | null>(null);
  const latestVolumeProfileRef = useRef<any>(null);
  const hasFitContentRef = useRef(false);
  const tradeLinesRef = useRef<any[]>([]);
  // Read (not reacted to) by effect 1 below to bound the overlay fetches to
  // the same lookback window actually on screen -- kept current every
  // render without adding `data` to effect 1's own dependency array.
  const dataLengthRef = useRef(data.length);
  dataLengthRef.current = data.length;

  useEffect(() => {
    if (!isFullscreen) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsFullscreen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isFullscreen]);

  // Effect 1: create the chart + fetch/draw every overlay (S/R, RSI
  // divergence, trend channel, liquidity zones, volume profile) -- keyed on
  // symbol+timeframe ONLY, not on `data`/`openTrades`/`opportunities`. Those
  // change far more often (a new candle tick, a trade opening/closing) than
  // the symbol being viewed does; previously this whole block re-ran on
  // every one of those changes too, tearing down and re-fetching every
  // overlay from scratch each time -- visibly flickering the S/R lines away
  // and back, and (worse, under Hyperliquid rate-limit pressure) leaving
  // them gone for minutes until the re-fetch finally succeeded. Confirmed
  // live 2026-08-21.
  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    let cancelled = false;
    setHandles(null);
    hasFitContentRef.current = false;
    latestVolumeProfileRef.current = null;

    const renderChart = async () => {
      try {
        const { createChart, ColorType, CandlestickSeries, LineSeries } = await import("lightweight-charts");
        if (cancelled) return;

        const chart = createChart(container, {
          width: container.clientWidth,
          height: container.clientHeight,
          layout: {
            background: { type: ColorType.Solid, color: "transparent" },
            textColor: "rgba(255,255,255,0.4)",
            fontSize: 10,
            fontFamily: "JetBrains Mono, monospace",
          },
          grid: {
            vertLines: { color: "rgba(255,255,255,0.03)" },
            horzLines: { color: "rgba(255,255,255,0.03)" },
          },
          crosshair: {
            vertLine: { color: "rgba(255,255,255,0.1)", width: 1, style: 2 },
            horzLine: { color: "rgba(255,255,255,0.1)", width: 1, style: 2 },
          },
          rightPriceScale: {
            borderColor: "rgba(255,255,255,0.06)",
            scaleMargins: { top: 0.05, bottom: 0.1 },
          },
          timeScale: {
            borderColor: "rgba(255,255,255,0.06)",
            timeVisible: true,
            secondsVisible: false,
          },
          handleScroll: false,
          handleScale: false,
        });

        const candleSeries = chart.addSeries(CandlestickSeries, {
          upColor: "rgba(34, 197, 94, 0.8)",
          downColor: "rgba(239, 68, 68, 0.8)",
          borderUpColor: "rgba(34, 197, 94, 0.8)",
          borderDownColor: "rgba(239, 68, 68, 0.8)",
          wickUpColor: "rgba(34, 197, 94, 0.4)",
          wickDownColor: "rgba(239, 68, 68, 0.4)",
        });

        // EMA20/EMA50 -- computed client-side from candle data (effect 2
        // pushes the actual values in); gives visual confirmation of the
        // trend_score ScoringEngine already computes server-side from these
        // same EMAs (scoring/scoring_engine.py).
        const ema20Series = chart.addSeries(LineSeries, {
          color: "rgba(250, 204, 21, 0.8)", // yellow-400
          lineWidth: 1 as LineWidth,
          priceLineVisible: false,
          lastValueVisible: false,
          title: "EMA20",
        });
        const ema50Series = chart.addSeries(LineSeries, {
          color: "rgba(236, 72, 153, 0.8)", // pink-500
          lineWidth: 1 as LineWidth,
          priceLineVisible: false,
          lastValueVisible: false,
          title: "EMA50",
        });

        // Volume Profile -- a horizontal volume-at-price histogram has no
        // native lightweight-charts series type (HistogramSeries is
        // volume-by-time along the bottom, not volume-by-price along the
        // side), so it's drawn as a plain <canvas> overlay positioned over
        // the chart, using the candle series' own priceToCoordinate() to
        // stay aligned with the real price scale.
        const volumeCanvas = document.createElement("canvas");
        volumeCanvas.style.position = "absolute";
        volumeCanvas.style.top = "0";
        volumeCanvas.style.left = "0";
        volumeCanvas.style.pointerEvents = "none";
        container.style.position = "relative";
        container.appendChild(volumeCanvas);

        const drawVolumeProfile = () => {
          const profile = latestVolumeProfileRef.current;
          const ctx = volumeCanvas.getContext("2d");
          if (!ctx) return;

          const dpr = window.devicePixelRatio || 1;
          const w = container.clientWidth;
          const h = container.clientHeight;
          volumeCanvas.width = w * dpr;
          volumeCanvas.height = h * dpr;
          volumeCanvas.style.width = `${w}px`;
          volumeCanvas.style.height = `${h}px`;
          ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
          ctx.clearRect(0, 0, w, h);

          if (!profile || profile.bins.length === 0) return;

          const maxVolume = Math.max(...profile.bins.map((b: any) => b.volume), 1e-9);
          // Was 22% -- reported as covering half the chart and drowning out
          // the candles themselves. Halved the width and every opacity
          // below (confirmed live 2026-08-21) so it reads as a subtle
          // backdrop, not the dominant visual element.
          const maxBarWidth = w * 0.12;

          profile.bins.forEach((bin: any) => {
            const yTop = candleSeries.priceToCoordinate(bin.price_high);
            const yBottom = candleSeries.priceToCoordinate(bin.price_low);
            if (yTop == null || yBottom == null) return;

            const isPoc = profile.poc_price != null
              && bin.price_low <= profile.poc_price && profile.poc_price <= bin.price_high;
            const inValueArea = profile.value_area_low != null && profile.value_area_high != null
              && bin.price_high >= profile.value_area_low && bin.price_low <= profile.value_area_high;

            ctx.fillStyle = isPoc
              ? "rgba(251, 191, 36, 0.30)" // amber -- Point of Control
              : inValueArea
                ? "rgba(99, 102, 241, 0.16)" // indigo -- Value Area (70% of volume)
                : "rgba(148, 163, 184, 0.09)"; // slate -- outside the value area

            const barWidth = Math.max(1, (bin.volume / maxVolume) * maxBarWidth);
            const top = Math.min(yTop, yBottom);
            const barHeight = Math.max(1, Math.abs(yBottom - yTop) - 1);
            ctx.fillRect(0, top, barWidth, barHeight);
          });
        };

        // Dynamically import fetch functions to draw overlays
        const {
          fetchMarketLevels, fetchMarketDivergence, fetchMarketChannel,
          fetchLiquidityZones, fetchVolumeProfile,
        } = await import("../../api/market");
        const symbolStr = symbol || "BTC";
        // Match the overlay lookback window to what's actually displayed --
        // see fetchMarketChannel()'s docstring for why a mismatch here is a
        // real, visible bug (a channel/divergence line anchored outside the
        // visible candle range renders disconnected from every candle).
        const overlayLimit = dataLengthRef.current > 0 ? dataLengthRef.current : undefined;

        // 1. Support/Resistance Levels
        const p1 = fetchMarketLevels(symbolStr, timeframe, overlayLimit)
          .then((levels) => {
            if (!levels || levels.length === 0) return;
            levels.forEach((lvl) => {
              const color = lvl.type === "support" ? "rgba(34, 197, 94, 0.7)" : "rgba(239, 68, 68, 0.7)";
              const lineWidth = Math.min(3, Math.max(1, Math.round(lvl.strength / 2))) as LineWidth;

              candleSeries.createPriceLine({
                price: lvl.price,
                color,
                lineWidth,
                lineStyle: 2, // Dashed lineStyle
                axisLabelVisible: true,
                title: `${lvl.type.toUpperCase()} (S:${lvl.strength})`,
              });
            });
          })
          .catch((err) => console.error("Error fetching S/R levels", err));

        // 2. RSI Divergence
        const p2 = fetchMarketDivergence(symbolStr, timeframe, overlayLimit)
          .then((div) => {
            if (!div || !div.found || !div.p1 || !div.p2) return;

            const color = div.type === "bullish" ? "rgba(34, 197, 94, 0.9)" : "rgba(239, 68, 68, 0.9)";
            const divSeries = chart.addSeries(LineSeries, {
              color,
              lineWidth: 3 as LineWidth,
              title: `${div.type.toUpperCase()} DIV`,
              priceLineVisible: false,
            });

            const t1 = div.p1.time > 1e10 ? Math.floor(div.p1.time / 1000) : div.p1.time;
            const t2 = div.p2.time > 1e10 ? Math.floor(div.p2.time / 1000) : div.p2.time;

            divSeries.setData([
              { time: t1 as any, value: div.p1.price },
              { time: t2 as any, value: div.p2.price },
            ]);
          })
          .catch((err) => console.error("Error fetching RSI divergence", err));

        // 3. Trend Channel
        const p3 = fetchMarketChannel(symbolStr, timeframe, overlayLimit)
          .then((chan) => {
            if (!chan || !chan.found || !chan.upper || !chan.lower) return;

            const color = "rgba(14, 165, 233, 0.8)"; // sky-500 consistent color

            const upperSeries = chart.addSeries(LineSeries, {
              color,
              lineWidth: 2 as LineWidth,
              priceLineVisible: false,
              title: `CHANNEL ${chan.direction.toUpperCase()}`,
            });
            const lowerSeries = chart.addSeries(LineSeries, {
              color,
              lineWidth: 2 as LineWidth,
              priceLineVisible: false,
            });

            const uStartT = chan.upper.start.time > 1e10 ? Math.floor(chan.upper.start.time / 1000) : chan.upper.start.time;
            const uEndT = chan.upper.end.time > 1e10 ? Math.floor(chan.upper.end.time / 1000) : chan.upper.end.time;

            const lStartT = chan.lower.start.time > 1e10 ? Math.floor(chan.lower.start.time / 1000) : chan.lower.start.time;
            const lEndT = chan.lower.end.time > 1e10 ? Math.floor(chan.lower.end.time / 1000) : chan.lower.end.time;

            upperSeries.setData([
              { time: uStartT as any, value: chan.upper.start.price },
              { time: uEndT as any, value: chan.upper.end.price },
            ]);

            lowerSeries.setData([
              { time: lStartT as any, value: chan.lower.start.price },
              { time: lEndT as any, value: chan.lower.end.price },
            ]);
          })
          .catch((err) => console.error("Error fetching Trend Channel", err));

        // 4. Swing liquidity pools (ICT/SMC concept) -- resting stop/
        // liquidation orders assumed to cluster just beyond swing points.
        // Reuses the same createPriceLine() pattern as S/R above, but with
        // its own colors (amber/violet) so the two concepts stay visually
        // distinct even though both render as horizontal lines.
        const p4 = fetchLiquidityZones(symbolStr, timeframe, overlayLimit)
          .then((zones) => {
            if (!zones || zones.length === 0) return;
            zones.forEach((zone) => {
              const isSellSide = zone.type === "sell_side";
              const color = isSellSide ? "rgba(245, 158, 11, 0.7)" : "rgba(168, 85, 247, 0.7)"; // amber / violet
              const lineWidth = Math.min(3, Math.max(1, zone.touches)) as LineWidth;
              candleSeries.createPriceLine({
                price: zone.price,
                color,
                lineWidth,
                lineStyle: 0, // Solid -- liquidity pools are a harder "the market wants this price" signal than dashed S/R
                axisLabelVisible: true,
                title: `${isSellSide ? "SSL" : "BSL"} x${zone.touches}`,
              });
            });
          })
          .catch((err) => console.error("Error fetching liquidity zones", err));

        // 5. Volume Profile
        const p5 = fetchVolumeProfile(symbolStr, timeframe, overlayLimit)
          .then((profile) => {
            latestVolumeProfileRef.current = profile;
            drawVolumeProfile();
          })
          .catch((err) => console.error("Error fetching volume profile", err));

        Promise.allSettled([p1, p2, p3, p4, p5]).then(() => onReady?.());

        // ResizeObserver (not a window "resize" listener) -- the chart's own
        // container can change size for reasons that never fire a window
        // resize event at all (sidebar collapsing, a sibling panel loading
        // in, a flex/grid reflow from unrelated layout changes), so relying
        // on window resize alone left the canvas stuck at whatever size it
        // happened to be created at.
        //
        // disposed guards against a real race: ResizeObserver can deliver an
        // already-queued callback even after disconnect() runs (it doesn't
        // synchronously cancel one in flight), which would call
        // chart.applyOptions() on an already-chart.remove()'d instance and
        // throw "Object is disposed". Set this before chart.remove() so the
        // callback becomes a no-op instead.
        //
        // ResizeObserver itself is guarded to exist first -- environments
        // without it (older browsers, jsdom in tests) must not throw here:
        // a throw at this point would skip the `return () => {...}` below
        // entirely, so `chart.remove()` would never run on unmount and the
        // chart's internal draw loop would keep firing indefinitely against
        // an already-torn-down container -- confirmed as the root cause of
        // a real CI failure (an uncaught "Value is null" from
        // lightweight-charts' internals, well after the test that rendered
        // it had already finished).
        let disposed = false;
        let resizeObserver: ResizeObserver | null = null;
        if (typeof ResizeObserver !== "undefined") {
          resizeObserver = new ResizeObserver((entries) => {
            if (disposed) return;
            const entry = entries[0];
            if (!entry) return;
            const { width, height } = entry.contentRect;
            if (width > 0 && height > 0) {
              chart.applyOptions({ width, height });
              drawVolumeProfile();
            }
          });
          resizeObserver.observe(container);
        }

        if (cancelled) {
          disposed = true;
          resizeObserver?.disconnect();
          chart.remove();
          if (container.contains(volumeCanvas)) container.removeChild(volumeCanvas);
          return;
        }

        setHandles({ chart, candleSeries, ema20Series, ema50Series, drawVolumeProfile });

        return () => {
          disposed = true;
          resizeObserver?.disconnect();
          chart.remove();
          if (container.contains(volumeCanvas)) {
            container.removeChild(volumeCanvas);
          }
        };
      } catch {
        // lightweight-charts not available
      }
    };

    const cleanupPromise = renderChart();
    return () => {
      cancelled = true;
      cleanupPromise.then((cleanup) => cleanup?.());
    };
  }, [symbol, timeframe]);

  // Effect 2: push fresh candle + EMA values onto the existing chart
  // instance whenever `data` changes -- no fetch, no teardown, so this can
  // run on every tick (a new WS candle, a poll refresh) without disturbing
  // the overlays effect 1 already fetched and drew.
  useEffect(() => {
    if (!handles || data.length === 0) return;

    handles.candleSeries.setData(data.map((d) => ({
      time: d.time as any,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
      volume: d.volume,
    })));

    if (data.length >= 2) {
      const closes = data.map((d) => d.close);
      handles.ema20Series.setData(
        computeEma(closes, 20).map((value, i) => ({ time: data[i].time as any, value }))
      );
      handles.ema50Series.setData(
        computeEma(closes, 50).map((value, i) => ({ time: data[i].time as any, value }))
      );
    }

    handles.drawVolumeProfile();

    // Only fit the visible range on the first paint after a chart is
    // (re)created -- doing this on every subsequent tick would keep
    // yanking the user's zoom/pan back to "fit everything" as new candles
    // stream in.
    if (!hasFitContentRef.current) {
      handles.chart.timeScale().fitContent();
      hasFitContentRef.current = true;
    }
  }, [handles, data]);

  // Effect 3: open-trade / scanner-opportunity price lines -- redrawn in
  // place (old ones removed first) whenever these change, without touching
  // the candles or any of the fetched overlays.
  useEffect(() => {
    if (!handles) return;
    const series = handles.candleSeries;

    openTrades.forEach((trade) => {
      const lines: [number | undefined, string, string][] = [
        [trade.entry, "rgba(255,255,255,0.5)", "ENTRY"],
        [trade.stop, "rgba(239, 68, 68, 0.8)", "STOP"],
        [trade.tp1, "rgba(34, 197, 94, 0.8)", "TP1"],
        [trade.tp2, "rgba(34, 197, 94, 0.5)", "TP2"],
      ];
      lines.forEach(([price, color, title]) => {
        if (!price) return;
        tradeLinesRef.current.push(series.createPriceLine({
          price,
          color,
          lineWidth: 2 as LineWidth,
          lineStyle: 3, // Dotted -- distinguishes an open-trade level from the dashed S/R lines
          axisLabelVisible: true,
          title,
        }));
      });
    });

    // Same real TPSLEngine levels a trade would get if this signal were
    // actually executed (scanner/core.py's _enrich_opportunities()), not a
    // real position yet. Thinner + a lower opacity than the open-trade
    // lines above so "the scanner is flagging this" reads as distinct from
    // "you're actually in this trade".
    opportunities.forEach((opp) => {
      const lines: [number | null | undefined, string, string][] = [
        [opp.price, "rgba(255,255,255,0.3)", "OPP ENTRY"],
        [opp.stop, "rgba(239, 68, 68, 0.4)", "OPP STOP"],
        [opp.tp1, "rgba(34, 197, 94, 0.4)", "OPP TP1"],
      ];
      lines.forEach(([price, color, title]) => {
        if (!price) return;
        tradeLinesRef.current.push(series.createPriceLine({
          price,
          color,
          lineWidth: 1 as LineWidth,
          lineStyle: 1, // Dashed -- distinguishes an unrealized opportunity from a real open-trade level
          axisLabelVisible: true,
          title,
        }));
      });
    });

    return () => {
      // The chart (and every price line on it) may already be gone by the
      // time this runs -- effect 1 tearing down for a symbol/timeframe
      // change removes the whole series before this cleanup fires. Removing
      // a line from an already-disposed series is a no-op we don't care
      // about, not a real failure.
      tradeLinesRef.current.forEach((line) => {
        try {
          series.removePriceLine(line);
        } catch {
          // series already disposed
        }
      });
      tradeLinesRef.current = [];
    };
  }, [handles, openTrades, opportunities]);

  if (data.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>{symbol}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64 text-sm text-[var(--text-muted)]">
            {t("chartPanel.empty")}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={isFullscreen ? "fixed inset-0 z-50 flex flex-col h-screen w-screen rounded-none" : "h-full"}>
      <CardHeader>
        <CardTitle>{symbol}</CardTitle>
        <button
          type="button"
          onClick={() => setIsFullscreen((v) => !v)}
          aria-label={t(isFullscreen ? "chartPanel.collapse" : "chartPanel.expand")}
          title={t(isFullscreen ? "chartPanel.collapse" : "chartPanel.expand")}
          className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
        >
          {isFullscreen ? <X size={14} /> : <Maximize2 size={14} />}
        </button>
      </CardHeader>
      <CardContent className={isFullscreen ? "p-0 flex-1 min-h-0" : "p-0"}>
        <div ref={containerRef} className={isFullscreen ? "w-full h-full" : "w-full h-[400px]"} />
      </CardContent>
    </Card>
  );
}

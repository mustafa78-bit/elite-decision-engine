import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import type { LineWidth } from "lightweight-charts";
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

interface ChartPanelProps {
  data?: Candle[];
  timeframe?: string;
  openTrades?: TradePayload[];
  opportunities?: ScannerOpportunity[];
}

export function ChartPanel({ data = [], timeframe = "1h", openTrades = [], opportunities = [] }: ChartPanelProps) {
  const { t } = useTranslation("tradingWorkspace");
  const containerRef = useRef<HTMLDivElement>(null);
  const { symbol } = useTerminalStore();

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    const container = containerRef.current;
    const renderChart = async () => {
      try {
        const { createChart, ColorType, CandlestickSeries, LineSeries } = await import("lightweight-charts");
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

        candleSeries.setData(data.map((d) => ({
          time: d.time as any,
          open: d.open,
          high: d.high,
          low: d.low,
          close: d.close,
          volume: d.volume,
        })));

        chart.timeScale().fitContent();

        // 0. Open trade entry/stop/target lines -- local data, no fetch
        // needed. Cleaned up automatically along with everything else on
        // chart.remove() below when data/symbol/timeframe/openTrades change.
        openTrades.forEach((trade) => {
          const lines: [number | undefined, string, string][] = [
            [trade.entry, "rgba(255,255,255,0.5)", "ENTRY"],
            [trade.stop, "rgba(239, 68, 68, 0.8)", "STOP"],
            [trade.tp1, "rgba(34, 197, 94, 0.8)", "TP1"],
            [trade.tp2, "rgba(34, 197, 94, 0.5)", "TP2"],
          ];
          lines.forEach(([price, color, title]) => {
            if (!price) return;
            candleSeries.createPriceLine({
              price,
              color,
              lineWidth: 2 as LineWidth,
              lineStyle: 3, // Dotted -- distinguishes an open-trade level from the dashed S/R lines below
              axisLabelVisible: true,
              title,
            });
          });
        });

        // 0b. Scanner opportunity entry/stop/target -- same real TPSLEngine
        // levels a trade would get if this signal were actually executed
        // (scanner/core.py's _enrich_opportunities()), not a real position
        // yet. Thinner + a lower opacity than the open-trade lines above so
        // "the scanner is flagging this" reads as distinct from "you're
        // actually in this trade".
        opportunities.forEach((opp) => {
          const lines: [number | null | undefined, string, string][] = [
            [opp.price, "rgba(255,255,255,0.3)", "OPP ENTRY"],
            [opp.stop, "rgba(239, 68, 68, 0.4)", "OPP STOP"],
            [opp.tp1, "rgba(34, 197, 94, 0.4)", "OPP TP1"],
          ];
          lines.forEach(([price, color, title]) => {
            if (!price) return;
            candleSeries.createPriceLine({
              price,
              color,
              lineWidth: 1 as LineWidth,
              lineStyle: 1, // Dashed -- distinguishes an unrealized opportunity from a real open-trade level
              axisLabelVisible: true,
              title,
            });
          });
        });

        // Dynamically import fetch functions to draw overlays
        const { fetchMarketLevels, fetchMarketDivergence, fetchMarketChannel } = await import("../../api/market");
        const symbolStr = symbol || "BTC";

        // 1. Support/Resistance Levels
        fetchMarketLevels(symbolStr, timeframe)
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
        fetchMarketDivergence(symbolStr, timeframe)
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
        fetchMarketChannel(symbolStr, timeframe)
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

        const handleResize = () => {
          chart.applyOptions({
            width: container.clientWidth,
            height: container.clientHeight,
          });
        };
        window.addEventListener("resize", handleResize);

        return () => {
          window.removeEventListener("resize", handleResize);
          chart.remove();
        };
      } catch {
        // lightweight-charts not available
      }
    };

    const cleanupPromise = renderChart();
    return () => {
      cleanupPromise.then((cleanup) => cleanup?.());
    };
  }, [data, symbol, timeframe, openTrades, opportunities]);

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
    <Card className="h-full">
      <CardHeader>
        <CardTitle>{symbol}</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div ref={containerRef} className="w-full h-[400px]" />
      </CardContent>
    </Card>
  );
}

import { useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { useTerminalStore } from "../../stores/terminal-store";

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
}

export function ChartPanel({ data = [] }: ChartPanelProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { symbol } = useTerminalStore();

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    const container = containerRef.current;
    const renderChart = async () => {
      try {
        const { createChart, ColorType } = await import("lightweight-charts");
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
          watermark: {
            visible: true,
            text: symbol,
            color: "rgba(255,255,255,0.03)",
            fontSize: 32,
            fontFamily: "JetBrains Mono",
          },
        });

        const candleSeries = chart.addCandlestickSeries({
          upColor: "rgba(34, 197, 94, 0.8)",
          downColor: "rgba(239, 68, 68, 0.8)",
          borderUpColor: "rgba(34, 197, 94, 0.8)",
          borderDownColor: "rgba(239, 68, 68, 0.8)",
          wickUpColor: "rgba(34, 197, 94, 0.4)",
          wickDownColor: "rgba(239, 68, 68, 0.4)",
        });

        candlestickSeries.setData(data.map((d) => ({
          time: d.time as any,
          open: d.open,
          high: d.high,
          low: d.low,
          close: d.close,
          volume: d.volume,
        })));

        chart.timeScale().fitContent();

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
  }, [data, symbol]);

  if (data.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>{symbol}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64 text-sm text-[var(--text-muted)]">
            No chart data available
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

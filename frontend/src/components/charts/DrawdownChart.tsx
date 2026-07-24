import { useEffect, useRef } from "react";
import { createChart, ColorType, AreaSeries } from "lightweight-charts";

interface Point {
  time: string;
  value: number;
}

interface Props {
  equityCurve: number[];
  height?: number;
}

export default function DrawdownChart({ equityCurve, height = 150 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  const drawdownData: Point[] = equityCurve.length > 0
    ? (() => {
        const peak = equityCurve[0];
        const points: Point[] = [{ time: "0", value: 0 }];
        let runningPeak = peak;
        for (let i = 1; i < equityCurve.length; i++) {
          const val = equityCurve[i];
          if (val > runningPeak) runningPeak = val;
          const dd = runningPeak > 0 ? ((runningPeak - val) / runningPeak) * 100 : 0;
          points.push({ time: String(i), value: -dd });
        }
        return points;
      })()
    : [];

  useEffect(() => {
    if (!containerRef.current || drawdownData.length === 0) return;

    const chart = createChart(containerRef.current, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#6b7280",
        fontSize: 12,
      },
      grid: { vertLines: { color: "#1f2937" }, horzLines: { color: "#1f2937" } },
      rightPriceScale: { borderColor: "#374151" },
      timeScale: { borderColor: "#374151", visible: false },
    });

    const series = chart.addSeries(AreaSeries, {
      lineColor: "#ef4444",
      topColor: "rgba(239, 68, 68, 0.3)",
      bottomColor: "rgba(239, 68, 68, 0.05)",
      lineWidth: 2,
      priceLineVisible: false,
    });

    series.setData(drawdownData);
    chart.timeScale().fitContent();

    return () => chart.remove();
  }, [drawdownData, height]);

  if (drawdownData.length === 0) {
    return (
      <div className="text-[var(--text-muted)] text-xs p-4 border border-dashed border-gray-800 rounded text-center">
        No drawdown data
      </div>
    );
  }

  return <div ref={containerRef} />;
}

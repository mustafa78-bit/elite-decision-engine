import { useEffect, useRef } from "react";
import { createChart, ColorType, HistogramSeries } from "lightweight-charts";

interface DataPoint {
  time: string;
  value: number;
}

interface Props {
  data: DataPoint[];
  height?: number;
}

export default function PnLChart({ data, height = 200 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    const chart = createChart(containerRef.current, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#6b7280",
        fontSize: 10,
      },
      grid: {
        vertLines: { color: "#1f2937" },
        horzLines: { color: "#1f2937" },
      },
      crosshair: { vertLine: { visible: false }, horzLine: { visible: false } },
      rightPriceScale: { borderColor: "#374151" },
      timeScale: { borderColor: "#374151", visible: false },
    });

    const series = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceLineVisible: false,
    });

    series.setData(
      data.map((d) => ({
        time: d.time,
        value: Math.abs(d.value),
        color: d.value >= 0 ? "#22c55e" : "#ef4444",
      })),
    );

    chart.timeScale().fitContent();

    return () => chart.remove();
  }, [data, height]);

  if (data.length === 0) {
    return (
      <div className="text-gray-500 text-xs p-4 border border-dashed border-gray-800 rounded text-center">
        No PnL data
      </div>
    );
  }

  return <div ref={containerRef} />;
}

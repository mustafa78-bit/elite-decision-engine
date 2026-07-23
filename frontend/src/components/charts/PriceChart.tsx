import { useEffect, useRef } from "react";
import { createChart, ColorType, LineSeries } from "lightweight-charts";

interface DataPoint {
  time: string;
  value: number;
}

interface Props {
  data: DataPoint[];
  color?: string;
  height?: number;
}

export default function PriceChart({ data, color = "#22c55e", height = 200 }: Props) {
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

    const series = chart.addSeries(LineSeries, {
      color,
      lineWidth: 2,
      crosshairMarkerVisible: false,
      priceLineVisible: false,
    });

    series.setData(data);

    chart.timeScale().fitContent();

    return () => chart.remove();
  }, [data, color, height]);

  if (data.length === 0) {
    return (
      <div className="text-[var(--text-muted)] text-xs p-4 border border-dashed border-gray-800 rounded text-center">
        No chart data
      </div>
    );
  }

  return <div ref={containerRef} />;
}

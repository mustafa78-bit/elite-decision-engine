import { useEffect, useRef } from "react";
import { createChart, ColorType, LineSeries } from "lightweight-charts";

interface LineData {
  time: string;
  value: number;
}

interface Props {
  equityCurve: LineData[];
  height?: number;
}

export default function PerformanceChart({ equityCurve, height = 200 }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || equityCurve.length === 0) return;

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
      color: "#3b82f6",
      lineWidth: 2,
      crosshairMarkerVisible: false,
      priceLineVisible: false,
    });

    series.setData(equityCurve);
    chart.timeScale().fitContent();

    return () => chart.remove();
  }, [equityCurve, height]);

  if (equityCurve.length === 0) {
    return (
      <div className="text-gray-500 text-xs p-4 border border-dashed border-gray-800 rounded text-center">
        No performance data
      </div>
    );
  }

  return <div ref={containerRef} />;
}

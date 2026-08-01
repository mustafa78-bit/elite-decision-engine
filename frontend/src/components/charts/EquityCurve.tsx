import { useEffect, useRef } from "react";
import { createChart, ColorType, LineSeries } from "lightweight-charts";

interface Point {
  time: string;
  value: number;
}

interface Props {
  data: Point[];
  height?: number;
}

export default function EquityCurve({ data, height = 200 }: Props) {
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
      grid: { vertLines: { color: "#1f2937" }, horzLines: { color: "#1f2937" } },
      rightPriceScale: { borderColor: "#374151" },
      timeScale: { borderColor: "#374151", visible: false },
    });

    const series = chart.addSeries(LineSeries, {
      color: "#3b82f6",
      lineWidth: 2,
      crosshairMarkerVisible: false,
      priceLineVisible: false,
    });

    series.setData(data);
    chart.timeScale().fitContent();

    return () => chart.remove();
  }, [data, height]);

  if (data.length === 0) {
    return (
      <div className="text-gray-500 text-xs p-4 border border-dashed border-gray-800 rounded text-center">
        No equity data
      </div>
    );
  }

  return <div ref={containerRef} />;
}

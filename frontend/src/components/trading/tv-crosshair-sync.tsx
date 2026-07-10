import { useEffect, useRef, useCallback } from "react";

interface CrosshairPosition {
  time: number;
  price: number;
}

interface TVCrosshairSyncProps {
  charts?: Array<{
    subscribeCrosshairMove: (handler: (param: any) => void) => void;
    unsubscribeCrosshairMove: (handler: (param: any) => void) => void;
    setCrosshairPosition: (time: number, price: number) => void;
    clearCrosshairPosition: () => void;
  }>;
  enabled?: boolean;
}

export function TVCrosshairSync({ charts = [], enabled = true }: TVCrosshairSyncProps) {
  const lastPos = useRef<CrosshairPosition | null>(null);
  const sourceIdx = useRef<number>(-1);

  const handleCrosshairMove = useCallback(
    (sourceIndex: number) => (param: any) => {
      if (!enabled || !param.time || !param.point) {
        charts.forEach((c, i) => {
          if (i !== sourceIdx.current) c.clearCrosshairPosition();
        });
        lastPos.current = null;
        sourceIdx.current = -1;
        return;
      }

      lastPos.current = { time: param.time as number, price: param.seriesPrices?.get?.() as number || 0 };
      sourceIdx.current = sourceIndex;

      charts.forEach((c, i) => {
        if (i !== sourceIndex && lastPos.current) {
          c.setCrosshairPosition(lastPos.current.time, lastPos.current.price);
        }
      });
    },
    [charts, enabled],
  );

  useEffect(() => {
    if (!enabled || charts.length < 2) return;
    const handlers = charts.map((c, i) => {
      const handler = handleCrosshairMove(i);
      c.subscribeCrosshairMove(handler);
      return { chart: c, handler };
    });
    return () => {
      handlers.forEach(({ chart, handler }) => {
        chart.unsubscribeCrosshairMove(handler);
      });
    };
  }, [charts, enabled, handleCrosshairMove]);

  return null;
}

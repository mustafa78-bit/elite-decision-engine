import { useOutletContext } from "react-router-dom";

import CandleStatus from "../components/live/CandleStatus";
import LivePriceCard from "../components/live/LivePriceCard";
import VolumeCard from "../components/live/VolumeCard";
import type { LayoutContext } from "../components/layout/Layout";

export default function LiveMarket() {
  const { latestPrice, latestCandle, latestVolume } = useOutletContext<LayoutContext>();

  const hasData = latestPrice || latestCandle || latestVolume;

  if (!hasData) {
    return (
      <div className="text-[var(--text-secondary)] text-xs p-6 border border-dashed border-[var(--border-subtle)] rounded text-center">
        Waiting for live data... connect to WebSocket
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">Live Market Feed</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {latestPrice && (
          <LivePriceCard
            symbol={latestPrice.symbol}
            price={latestPrice.price}
            change24h={latestPrice.change_24h}
          />
        )}
        {latestCandle && (
          <CandleStatus
            open={latestCandle.open}
            high={latestCandle.high}
            low={latestCandle.low}
            close={latestCandle.close}
            volume={latestCandle.volume}
          />
        )}
        {latestVolume && (
          <VolumeCard volume24h={latestVolume.volume_24h} symbol={latestVolume.symbol} />
        )}
      </div>
    </div>
  );
}

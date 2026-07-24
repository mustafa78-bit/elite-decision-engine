import { useCallback, useEffect, useState } from "react";

import BTCHealthCard from "../components/market/BTCHealthCard";
import MarketCard from "../components/market/MarketCard";
import { apiFetch, ApiError } from "../api/client";
import { PageHeader } from "../components/ui/PageHeader";
import { EmptyState } from "../components/ui/EmptyState";

interface MarketData {
  symbol: string;
  price: number;
  regime: string;
  regime_score: number;
  volatility: number;
  volatility_score: number;
  btc_health_score: number;
  ema20: number;
  ema50: number;
  ema200: number;
  rsi: number;
  atr: number;
  error?: string;
}

export default function Market() {
  const [data, setData] = useState<MarketData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMarket = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const d = await apiFetch<MarketData>("/market");
      if (d.error) {
        setError(d.error);
        return;
      }
      setData(d);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load market data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchMarket(); }, [fetchMarket]);

  if (loading) {
    return (
      <div className="space-y-4">
        <PageHeader
          title="Market Intelligence"
          subtitle="Comprehensive technical regime, volatility, and asset health"
        />
        <EmptyState
          loading
          title="Loading market data..."
          description="Fetching technical indicators and volatility metrics from the streaming feed."
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <PageHeader
          title="Market Intelligence"
          subtitle="Comprehensive technical regime, volatility, and asset health"
        />
        <EmptyState
          title="No market data available"
          description="The market intelligence service is currently unavailable. Reconnect or try again shortly."
          error={error}
          actionButton={{
            label: "Retry connection",
            onClick: fetchMarket,
          }}
        />
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Market Intelligence"
        subtitle="Comprehensive technical regime, volatility, and asset health"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <MarketCard
          symbol={data.symbol}
          price={data.price}
          regime={data.regime}
          rsi={data.rsi}
          atr={data.atr}
        />
        <div className="lg:col-span-2">
          <BTCHealthCard
            btcHealthScore={data.btc_health_score}
            ema20={data.ema20}
            ema50={data.ema50}
            ema200={data.ema200}
            volatility={data.volatility}
            volatilityScore={data.volatility_score}
            regimeScore={data.regime_score}
          />
        </div>
      </div>
    </div>
  );
}

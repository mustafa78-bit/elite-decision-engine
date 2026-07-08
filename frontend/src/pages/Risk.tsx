import { useCallback, useEffect, useState } from "react";

import ExposureCard from "../components/risk/ExposureCard";
import PositionSizeCard from "../components/risk/PositionSizeCard";
import RiskCard from "../components/risk/RiskCard";
import type { RiskData, PositionSizing } from "../api/risk";
import { ApiError } from "../api/client";
import { fetchRisk, fetchPositionSizing } from "../api/risk";

export default function Risk() {
  const [risk, setRisk] = useState<RiskData | null>(null);
  const [sizing, setSizing] = useState<PositionSizing | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [entry, setEntry] = useState(50000);
  const [atr, setAtr] = useState(800);

  const fetchRiskData = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await fetchRisk();
      setRisk(data);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load risk data");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchSizing = useCallback(async (e: number, a: number) => {
    try {
      const data = await fetchPositionSizing(e, a);
      setSizing(data);
    } catch {
      // silently fail for interactive widget
    }
  }, []);

  useEffect(() => { fetchRiskData(); }, [fetchRiskData]);

  useEffect(() => {
    if (entry > 0) {
      const timer = setTimeout(() => fetchSizing(entry, atr), 300);
      return () => clearTimeout(timer);
    }
  }, [entry, atr, fetchSizing]);

  if (loading) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        Loading risk data...
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-red-400 text-xs p-4 border border-red-900 bg-red-950/30 rounded">
          {error}
          <button onClick={fetchRiskData} className="ml-2 underline text-gray-400 hover:text-gray-200">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!risk) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        No risk data available
      </div>
    );
  }

  const openPct = risk.max_open_trades > 0
    ? Math.round((risk.open_trades / risk.max_open_trades) * 100)
    : 0;
  const lossPct = risk.max_daily_loss > 0
    ? Math.round((Math.abs(risk.daily_loss) / risk.max_daily_loss) * 100)
    : 0;

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-3">
          Risk Overview
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          <RiskCard
            label="Risk Score"
            value={(risk.risk_score * 100).toFixed(0)}
            sub="/ 100"
            negative={risk.risk_score < 0.5}
          />
          <RiskCard
            label="Open Trades"
            value={`${risk.open_trades} / ${risk.max_open_trades}`}
            sub={`${openPct}% used`}
            negative={risk.open_trades >= risk.max_open_trades}
          />
          <RiskCard
            label="Daily Loss"
            value={`$${Math.abs(risk.daily_loss).toFixed(0)}`}
            sub={`${lossPct}% of limit`}
            negative={risk.daily_loss < 0}
          />
          <RiskCard
            label="Account Equity"
            value={`$${risk.account_equity.toLocaleString()}`}
          />
          <RiskCard
            label="Risk / Trade"
            value={`${risk.risk_per_trade_percent}%`}
            sub={`$${(risk.account_equity * risk.risk_per_trade_percent / 100).toFixed(0)} max`}
          />
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section>
          <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-3">
            Exposure
          </h2>
          <ExposureCard
            symbolExposure={risk.symbol_exposure}
            maxSymbolExposure={risk.max_symbol_exposure}
            portfolioExposure={risk.portfolio_exposure}
            maxPortfolioExposure={risk.max_portfolio_exposure}
          />
        </section>

        <section>
          <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-3">
            Position Sizing
          </h2>
          <PositionSizeCard
            entry={entry}
            atr={atr}
            onEntryChange={setEntry}
            onAtrChange={setAtr}
            quantity={sizing ? sizing.quantity.toFixed(6) : "\u2014"}
            notional={sizing ? sizing.notional_value.toFixed(2) : "\u2014"}
            riskAmount={sizing ? sizing.risk_amount.toFixed(2) : "\u2014"}
          />
        </section>
      </div>
    </div>
  );
}

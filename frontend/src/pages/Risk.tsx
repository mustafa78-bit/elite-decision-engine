import { useCallback, useEffect, useState } from "react";

import ExposureCard from "../components/risk/ExposureCard";
import PositionSizeCard from "../components/risk/PositionSizeCard";
import RiskCard from "../components/risk/RiskCard";

interface RiskData {
  risk_score: number;
  open_trades: number;
  max_open_trades: number;
  symbol_exposure: Record<string, number>;
  max_symbol_exposure: number;
  portfolio_exposure: number;
  max_portfolio_exposure: number;
  daily_loss: number;
  max_daily_loss: number;
  max_position_size_usd: number;
  account_equity: number;
  risk_per_trade_percent: number;
}

interface PositionSizing {
  quantity: number;
  notional_value: number;
  risk_amount: number;
}

const API = "http://localhost:8000";

export default function Risk() {
  const [risk, setRisk] = useState<RiskData | null>(null);
  const [sizing, setSizing] = useState<PositionSizing | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [entry, setEntry] = useState(50000);
  const [atr, setAtr] = useState(800);

  const fetchRisk = useCallback(async () => {
    try {
      setError(null);
      const res = await fetch(`${API}/risk`);
      if (!res.ok) throw new Error(`Risk API error: ${res.status}`);
      setRisk(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load risk data");
    }
  }, []);

  const fetchSizing = useCallback(async (e: number, a: number) => {
    try {
      const res = await fetch(`${API}/position-sizing?entry=${e}&atr=${a}`);
      if (!res.ok) return;
      setSizing(await res.json());
    } catch {
      // silently fail for interactive widget
    }
  }, []);

  useEffect(() => { fetchRisk(); }, [fetchRisk]);

  useEffect(() => {
    if (entry > 0) {
      const timer = setTimeout(() => fetchSizing(entry, atr), 300);
      return () => clearTimeout(timer);
    }
  }, [entry, atr, fetchSizing]);

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-red-400 text-xs p-4 border border-red-900 bg-red-950/30 rounded">
          {error}
          <button onClick={fetchRisk} className="ml-2 underline text-gray-400 hover:text-gray-200">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!risk) {
    return (
      <div className="text-gray-500 text-xs p-6 border border-dashed border-gray-800 rounded text-center">
        Loading risk data...
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

import { useCallback, useEffect, useState } from "react";

import ExposureCard from "../components/risk/ExposureCard";
import PositionSizeCard from "../components/risk/PositionSizeCard";
import RiskCard from "../components/risk/RiskCard";
import type { RiskData, PositionSizing } from "../api/risk";
import { ApiError } from "../api/client";
import { fetchRisk, fetchPositionSizing } from "../api/risk";
import { PageHeader } from "../components/ui/PageHeader";
import { EmptyState } from "../components/ui/EmptyState";

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
      <div className="space-y-4">
        <PageHeader
          title="Risk Management"
          subtitle="Account risk metrics, symbol exposure thresholds, and sizing"
        />
        <EmptyState
          loading
          title="Loading risk metrics..."
          description="Evaluating portfolio-wide VaR limits, leverage parameters, and drawdown thresholds."
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <PageHeader
          title="Risk Management"
          subtitle="Account risk metrics, symbol exposure thresholds, and sizing"
        />
        <EmptyState
          title="No risk data available"
          description="The risk assessment service is currently unavailable. Reconnect or try again shortly."
          error={error}
          actionButton={{
            label: "Retry connection",
            onClick: fetchRiskData,
          }}
        />
      </div>
    );
  }

  if (!risk) {
    return (
      <div className="space-y-4">
        <PageHeader
          title="Risk Management"
          subtitle="Account risk metrics, symbol exposure thresholds, and sizing"
        />
        <EmptyState
          title="No risk data available"
          description="The current user account has no active leverage or portfolio exposure configurations registered."
        />
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
      <PageHeader
        title="Risk Management"
        subtitle="Account risk metrics, symbol exposure thresholds, and sizing"
      />

      <section>
        <div className="flex items-center justify-between pb-2 mb-3 border-b border-[var(--border-subtle)]">
          <h2 className="text-xs uppercase tracking-[0.12em] font-semibold text-[var(--text-primary)]">
            Risk Overview
          </h2>
        </div>
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
          <div className="flex items-center justify-between pb-2 mb-3 border-b border-[var(--border-subtle)]">
            <h2 className="text-xs uppercase tracking-[0.12em] font-semibold text-[var(--text-primary)]">
              Exposure
            </h2>
          </div>
          <ExposureCard
            symbolExposure={risk.symbol_exposure}
            maxSymbolExposure={risk.max_symbol_exposure}
            portfolioExposure={risk.portfolio_exposure}
            maxPortfolioExposure={risk.max_portfolio_exposure}
          />
        </section>

        <section>
          <div className="flex items-center justify-between pb-2 mb-3 border-b border-[var(--border-subtle)]">
            <h2 className="text-xs uppercase tracking-[0.12em] font-semibold text-[var(--text-primary)]">
              Position Sizing
            </h2>
          </div>
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

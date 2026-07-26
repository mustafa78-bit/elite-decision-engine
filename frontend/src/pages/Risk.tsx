import { useCallback, useEffect, useState } from "react";

import ExposureCard from "../components/risk/ExposureCard";
import PositionSizeCard from "../components/risk/PositionSizeCard";
import RiskCard from "../components/risk/RiskCard";
import type { RiskData, PositionSizing } from "../api/risk";
import { ApiError } from "../api/client";
import { fetchRisk, fetchPositionSizing } from "../api/risk";
import { LoadingScreen } from "../components/layout/LoadingScreen";
import { ErrorState } from "../components/ui/ErrorState";
import { EmptyState } from "../components/ui/EmptyState";
import { PageHeader, PageContainer } from "../components/ui/PageHeader";

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
      <PageContainer>
        <PageHeader title="Risk" subtitle="Systemic Exposure & Position Sizing Guardrails" />
        <LoadingScreen variant="grid" />
      </PageContainer>
    );
  }

  if (error) {
    return (
      <PageContainer>
        <PageHeader title="Risk" subtitle="Systemic Exposure & Position Sizing Guardrails" />
        <ErrorState message={error} onRetry={fetchRiskData} />
      </PageContainer>
    );
  }

  if (!risk) {
    return (
      <PageContainer>
        <PageHeader title="Risk" subtitle="Systemic Exposure & Position Sizing Guardrails" />
        <EmptyState
          title="No Risk Parameters"
          description="Operational risk guidelines and current systemic parameters could not be fetched."
        />
      </PageContainer>
    );
  }

  const openPct = risk.max_open_trades > 0
    ? Math.round((risk.open_trades / risk.max_open_trades) * 100)
    : 0;
  const lossPct = risk.max_daily_loss > 0
    ? Math.round((Math.abs(risk.daily_loss) / risk.max_daily_loss) * 100)
    : 0;

  return (
    <PageContainer>
      <PageHeader title="Risk" subtitle="Systemic Exposure & Position Sizing Guardrails" />

      <section className="space-y-3">
        <h2 className="text-[10px] uppercase tracking-widest text-[var(--text-secondary)] font-semibold">
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
        <section className="space-y-3">
          <h2 className="text-[10px] uppercase tracking-widest text-[var(--text-secondary)] font-semibold">
            Exposure
          </h2>
          <ExposureCard
            symbolExposure={risk.symbol_exposure}
            maxSymbolExposure={risk.max_symbol_exposure}
            portfolioExposure={risk.portfolio_exposure}
            maxPortfolioExposure={risk.max_portfolio_exposure}
          />
        </section>

        <section className="space-y-3">
          <h2 className="text-[10px] uppercase tracking-widest text-[var(--text-secondary)] font-semibold">
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
    </PageContainer>
  );
}

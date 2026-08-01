import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface TradeRow {
  date: string;
  side: string;
  entry: number;
  exit: number;
  pnl: number;
  pnlPercent: number;
  win: boolean;
}

interface BacktestResultViewerProps {
  strategyName?: string;
  summary?: {
    totalTrades: number;
    winRate: number;
    profitFactor: number;
    sharpeRatio: number;
    maxDrawdown: number;
    netProfit: number;
  };
  trades?: TradeRow[];
}

export function BacktestResultViewer({
  strategyName = "EMA Crossover",
  summary = {
    totalTrades: 147,
    winRate: 62.6,
    profitFactor: 1.84,
    sharpeRatio: 1.42,
    maxDrawdown: -8.3,
    netProfit: 12450,
  },
  trades = [
    { date: "2026-01-15", side: "LONG", entry: 42350, exit: 44120, pnl: 1770, pnlPercent: 4.18, win: true },
    { date: "2026-01-14", side: "SHORT", entry: 43800, exit: 43200, pnl: 600, pnlPercent: 1.37, win: true },
    { date: "2026-01-13", side: "LONG", entry: 41500, exit: 42100, pnl: 600, pnlPercent: 1.45, win: true },
    { date: "2026-01-12", side: "LONG", entry: 42800, exit: 41550, pnl: -1250, pnlPercent: -2.92, win: false },
    { date: "2026-01-11", side: "SHORT", entry: 44500, exit: 43200, pnl: 1300, pnlPercent: 2.92, win: true },
  ],
}: BacktestResultViewerProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>{strategyName}</CardTitle>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">Backtest Results</span>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="grid grid-cols-3 gap-1">
          {[
            { label: "Win Rate", value: `${summary.winRate}%`, color: "text-[var(--accent-green)]" },
            { label: "Profit Factor", value: summary.profitFactor.toFixed(2), color: "text-[var(--accent-blue)]" },
            { label: "Sharpe", value: summary.sharpeRatio.toFixed(2), color: "text-[var(--accent-blue)]" },
            { label: "Max DD", value: `${summary.maxDrawdown}%`, color: "text-[var(--accent-red)]" },
            { label: "Trades", value: summary.totalTrades, color: "text-[var(--text-secondary)]" },
            { label: "Net PnL", value: `$${summary.netProfit.toLocaleString()}`, color: "text-[var(--accent-green)]" },
          ].map((s) => (
            <div key={s.label} className="p-1 rounded bg-[var(--bg-base)] border border-[var(--border-subtle)] text-center">
              <div className="text-[8px] font-mono text-[var(--text-muted)] uppercase">{s.label}</div>
              <div className={`text-[11px] font-mono font-bold tabular-nums ${s.color}`}>{s.value}</div>
            </div>
          ))}
        </div>
        <div className="max-h-32 overflow-y-auto space-y-0.5">
          {trades.map((t, i) => (
            <div key={i} className="flex items-center justify-between px-2 py-0.5 text-[9px] font-mono rounded hover:bg-[var(--bg-hover)]">
              <span className="text-[var(--text-muted)] w-16">{t.date}</span>
              <Badge variant={t.side === "LONG" ? "success" : "danger"} className="text-[7px] w-10 text-center">{t.side}</Badge>
              <span className="tabular-nums w-20 text-right">${t.entry} → ${t.exit}</span>
              <span className={`tabular-nums w-16 text-right ${t.win ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                {t.pnl >= 0 ? "+" : ""}${t.pnl}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

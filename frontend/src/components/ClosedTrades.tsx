import type { TradePayload } from "../types/trade";

interface Props {
  trades: TradePayload[];
}

export default function ClosedTrades({ trades }: Props) {
  if (trades.length === 0) {
    return (
      <div className="glass-card px-4 py-5 text-center">
        <span className="text-[10px] font-mono" style={{ color: "var(--text-muted)" }}>No closed trades</span>
      </div>
    );
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-[11px] font-mono" style={{ borderCollapse: "collapse" }}>
          <thead>
            <tr className="text-[9px] uppercase tracking-[0.08em]" style={{ color: "var(--text-muted)", borderBottom: "1px solid #243244" }}>
              <th className="text-left px-4 py-2 font-medium">Symbol</th>
              <th className="text-left px-4 py-2 font-medium">Status</th>
              <th className="text-right px-4 py-2 font-medium">Exit</th>
              <th className="text-right px-4 py-2 font-medium">PnL</th>
              <th className="text-left px-4 py-2 font-medium">Reason</th>
            </tr>
          </thead>
          <tbody>
            {[...trades].reverse().map((t, i) => (
              <tr
                key={t.trade_id ?? i}
                style={{
                  borderBottom: "1px solid #243244",
                  transition: "background 0.15s ease",
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.03)"}
                onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
              >
                <td className="px-4 py-2 font-medium" style={{ color: "var(--text-primary)" }}>{t.symbol}</td>
                <td className="px-4 py-2" style={{ color: "var(--text-muted)" }}>{t.status}</td>
                <td className="px-4 py-2 text-right tabular-nums" style={{ color: "var(--text-secondary)" }}>{t.exit_price ?? "—"}</td>
                <td className="px-4 py-2 text-right tabular-nums">
                  {t.pnl != null ? (
                    <span style={{ color: t.pnl >= 0 ? "var(--accent-green)" : "var(--accent-red)" }}>
                      {t.pnl.toFixed(2)}
                    </span>
                  ) : "—"}
                </td>
                <td className="px-4 py-2" style={{ color: "var(--text-muted)" }}>{t.close_reason ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
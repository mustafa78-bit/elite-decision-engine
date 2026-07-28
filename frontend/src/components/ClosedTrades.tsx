import { useNavigate } from "react-router-dom";
import type { TradePayload } from "../types/trade";

interface Props {
  trades: TradePayload[];
}

export default function ClosedTrades({ trades }: Props) {
  const navigate = useNavigate();
  if (trades.length === 0) {
    return (
      <div className="glass-card px-4 py-5 text-center">
        <span className="text-[10px] font-mono" style={{ color: "#64748B" }}>No closed trades</span>
      </div>
    );
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-[11px] font-mono" style={{ borderCollapse: "collapse" }}>
          <thead>
            <tr className="text-[9px] uppercase tracking-[0.08em]" style={{ color: "#64748B", borderBottom: "1px solid #243244" }}>
              <th className="text-left px-4 py-2 font-medium">Symbol</th>
              <th className="text-left px-4 py-2 font-medium">Status</th>
              <th className="text-right px-4 py-2 font-medium">Exit</th>
              <th className="text-right px-4 py-2 font-medium">PnL</th>
              <th className="text-left px-4 py-2 font-medium">Reason</th>
              <th className="text-right px-4 py-2 font-medium">Action</th>
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
                <td className="px-4 py-2 font-medium" style={{ color: "#F1F5F9" }}>{t.symbol}</td>
                <td className="px-4 py-2" style={{ color: "#64748B" }}>{t.status}</td>
                <td className="px-4 py-2 text-right tabular-nums" style={{ color: "#94A3B8" }}>{t.exit_price ?? "—"}</td>
                <td className="px-4 py-2 text-right tabular-nums">
                  {t.pnl != null ? (
                    <span style={{ color: t.pnl >= 0 ? "#22C55E" : "#EF4444" }}>
                      {t.pnl.toFixed(2)}
                    </span>
                  ) : "—"}
                </td>
                <td className="px-4 py-2" style={{ color: "#64748B" }}>{t.close_reason ?? "—"}</td>
                <td className="px-4 py-2 text-right">
                  <button
                    onClick={() => {
                      const res = t.pnl !== undefined && t.pnl >= 0 ? "WIN" : "LOSS";
                      navigate(`/journal?symbol=${t.symbol}&side=${t.side}&entry_price=${t.entry}&exit_price=${t.exit_price ?? 0}&pnl=${t.pnl ?? 0}&result=${res}`);
                    }}
                    className="text-[9px] uppercase tracking-wider font-bold text-[var(--accent-blue)] bg-[var(--accent-blue)]/10 hover:bg-[var(--accent-blue)]/20 px-2 py-0.5 rounded transition-colors"
                  >
                    Journal 📓
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
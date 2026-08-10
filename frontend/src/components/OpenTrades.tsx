import { useTranslation } from "react-i18next";
import type { TradePayload } from "../types/trade";

interface Props {
  trades: TradePayload[];
}

export default function OpenTrades({ trades }: Props) {
  const { t } = useTranslation("trades");

  if (trades.length === 0) {
    return (
      <div className="glass-card px-4 py-5 text-center">
        <span className="text-[10px] font-mono" style={{ color: "#64748B" }}>{t("openTrades.empty")}</span>
      </div>
    );
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-[11px] font-mono" style={{ borderCollapse: "collapse" }}>
          <thead>
            <tr className="text-[9px] uppercase tracking-[0.08em]" style={{ color: "#64748B", borderBottom: "1px solid #243244" }}>
              <th className="text-left px-4 py-2 font-medium">{t("openTrades.columns.symbol")}</th>
              <th className="text-left px-4 py-2 font-medium">{t("openTrades.columns.side")}</th>
              <th className="text-right px-4 py-2 font-medium">{t("openTrades.columns.entry")}</th>
              <th className="text-left px-4 py-2 font-medium">{t("openTrades.columns.status")}</th>
            </tr>
          </thead>
          <tbody>
            {[...trades].reverse().map((trade, i) => (
              <tr
                key={trade.trade_id ?? i}
                style={{
                  borderBottom: "1px solid #243244",
                  transition: "background 0.15s ease",
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.03)"}
                onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
              >
                <td className="px-4 py-2 font-medium" style={{ color: "#F1F5F9" }}>{trade.symbol}</td>
                <td className="px-4 py-2">
                  <span style={{ color: trade.side === "LONG" ? "#22C55E" : "#EF4444" }}>{trade.side}</span>
                </td>
                <td className="px-4 py-2 text-right tabular-nums" style={{ color: "#94A3B8" }}>{trade.entry}</td>
                <td className="px-4 py-2" style={{ color: "#64748B" }}>{trade.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

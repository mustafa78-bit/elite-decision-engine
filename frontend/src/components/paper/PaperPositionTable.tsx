import { useTranslation } from "react-i18next";

import type { PaperTrade } from "../../api/paper";

interface Props {
  trades: PaperTrade[];
  title: string;
}

export default function PaperPositionTable({ trades, title }: Props) {
  const { t } = useTranslation("paperTrading");

  if (trades.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded p-4">
        <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">{title}</h3>
        <p className="text-gray-600 text-xs text-center py-4">{t("paperPositionTable.noTrades", { title })}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded overflow-hidden">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 px-4 pt-3 pb-2">
        {title} ({trades.length})
      </h3>
      <table className="w-full text-xs">
        <thead>
          <tr className="border-t border-b border-gray-800 text-gray-500 text-[10px] uppercase tracking-wider">
            <th className="text-left px-3 py-1.5 font-medium">{t("paperPositionTable.columns.symbol")}</th>
            <th className="text-left px-3 py-1.5 font-medium">{t("paperPositionTable.columns.side")}</th>
            <th className="text-right px-3 py-1.5 font-medium">{t("paperPositionTable.columns.entry")}</th>
            <th className="text-right px-3 py-1.5 font-medium">{t("paperPositionTable.columns.exit")}</th>
            <th className="text-right px-3 py-1.5 font-medium">{t("paperPositionTable.columns.pnl")}</th>
            <th className="text-right px-3 py-1.5 font-medium">{t("paperPositionTable.columns.status")}</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((trade) => (
            <tr key={trade.id} className="border-t border-gray-800/50 hover:bg-gray-800/30">
              <td className="px-3 py-1.5 text-gray-200">{trade.symbol}</td>
              <td className={`px-3 py-1.5 ${trade.side === "LONG" ? "text-green-400" : "text-red-400"}`}>
                {trade.side}
              </td>
              <td className="px-3 py-1.5 text-right text-gray-300 tabular-nums">
                ${trade.entry?.toFixed(2) ?? "—"}
              </td>
              <td className="px-3 py-1.5 text-right text-gray-300 tabular-nums">
                {trade.exit_price != null ? `$${trade.exit_price.toFixed(2)}` : "—"}
              </td>
              <td className={`px-3 py-1.5 text-right tabular-nums ${trade.pnl != null && trade.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                {trade.pnl != null ? `$${trade.pnl.toFixed(2)}` : "—"}
              </td>
              <td className="px-3 py-1.5 text-right text-gray-300">{trade.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

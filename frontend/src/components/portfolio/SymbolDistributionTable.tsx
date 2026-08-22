import { useTranslation } from "react-i18next";

import type { PortfolioDistributionBySymbol } from "../../types/api/portfolio";

interface Props {
  bySymbol: PortfolioDistributionBySymbol[];
}

export default function SymbolDistributionTable({ bySymbol }: Props) {
  const { t } = useTranslation("portfolio");

  if (bySymbol.length === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded p-4">
        <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">
          {t("distributionTable.title")}
        </h3>
        <p className="text-gray-600 text-xs text-center py-4">{t("distributionTable.noData")}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded overflow-hidden">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 px-4 pt-3 pb-2">
        {t("distributionTable.title")}
      </h3>
      <table className="w-full text-xs">
        <thead>
          <tr className="border-t border-b border-gray-800 text-gray-500 text-[10px] uppercase tracking-wider">
            <th className="text-left px-3 py-1.5 font-medium">{t("distributionTable.columns.symbol")}</th>
            <th className="text-right px-3 py-1.5 font-medium">{t("distributionTable.columns.trades")}</th>
            <th className="text-right px-3 py-1.5 font-medium">{t("distributionTable.columns.winRate")}</th>
            <th className="text-right px-3 py-1.5 font-medium">{t("distributionTable.columns.pnl")}</th>
          </tr>
        </thead>
        <tbody>
          {bySymbol.map((s) => (
            <tr key={s.symbol} className="border-t border-gray-800/50 hover:bg-gray-800/30">
              <td className="px-3 py-1.5 text-gray-200">{s.symbol}</td>
              <td className="px-3 py-1.5 text-right text-gray-300 tabular-nums">{s.trades}</td>
              <td className="px-3 py-1.5 text-right text-gray-300 tabular-nums">{s.win_rate.toFixed(1)}%</td>
              <td className={`px-3 py-1.5 text-right tabular-nums ${s.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                ${s.pnl.toFixed(2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

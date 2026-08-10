import { useTranslation } from "react-i18next";

interface Props {
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
  totalPnl: number;
  averageWin: number;
  averageLoss: number;
  profitFactor: number;
  maxDrawdown: number;
}

export default function PerformanceSummary({
  totalTrades,
  winningTrades,
  losingTrades,
  winRate,
  totalPnl,
  averageWin,
  averageLoss,
  profitFactor,
  maxDrawdown,
}: Props) {
  const { t } = useTranslation("analytics");
  const items = [
    { label: t("performanceSummary.items.totalTrades"), value: String(totalTrades) },
    { label: t("performanceSummary.items.winning"), value: String(winningTrades), color: "text-green-400" },
    { label: t("performanceSummary.items.losing"), value: String(losingTrades), color: "text-red-400" },
    { label: t("performanceSummary.items.winRate"), value: `${winRate.toFixed(1)}%` },
    { label: t("performanceSummary.items.totalPnl"), value: `$${totalPnl.toFixed(2)}`, color: totalPnl >= 0 ? "text-green-400" : "text-red-400" },
    { label: t("performanceSummary.items.avgWin"), value: `$${averageWin.toFixed(2)}`, color: "text-green-400" },
    { label: t("performanceSummary.items.avgLoss"), value: `$${averageLoss.toFixed(2)}`, color: "text-red-400" },
    { label: t("performanceSummary.items.profitFactor"), value: profitFactor.toFixed(2) },
    { label: t("performanceSummary.items.maxDrawdown"), value: `${maxDrawdown.toFixed(1)}%`, color: "text-red-400" },
  ];

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">
        {t("performanceSummary.title")}
      </h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-4 gap-y-2">
        {items.map((item) => (
          <div key={item.label}>
            <div className="text-[9px] text-gray-600 uppercase tracking-wider">{item.label}</div>
            <div className={`text-sm font-semibold tabular-nums ${item.color || "text-gray-200"}`}>
              {item.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

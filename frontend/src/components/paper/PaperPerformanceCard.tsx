import { useTranslation } from "react-i18next";

interface Props {
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  winRate: number;
}

export default function PaperPerformanceCard({ totalTrades, winningTrades, losingTrades, winRate }: Props) {
  const { t } = useTranslation("paperTrading");
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">
        {t("paperPerformanceCard.title")}
      </h3>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">{t("paperPerformanceCard.total")}</div>
          <div className="text-gray-200 font-semibold tabular-nums">{totalTrades}</div>
        </div>
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">{t("paperPerformanceCard.winRate")}</div>
          <div className="text-green-400 font-semibold tabular-nums">{winRate.toFixed(1)}%</div>
        </div>
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">{t("paperPerformanceCard.wins")}</div>
          <div className="text-green-400 font-semibold tabular-nums">{winningTrades}</div>
        </div>
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">{t("paperPerformanceCard.losses")}</div>
          <div className="text-red-400 font-semibold tabular-nums">{losingTrades}</div>
        </div>
      </div>
    </div>
  );
}

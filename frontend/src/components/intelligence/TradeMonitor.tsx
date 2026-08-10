import { useTranslation } from "react-i18next";

interface Props {
  open: number;
  closed: number;
  totalPnl: number;
}

export default function TradeMonitor({ open, closed, totalPnl }: Props) {
  const { t } = useTranslation("intelligence");

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">{t("tradeMonitor.title")}</h3>
      <div className="grid grid-cols-3 gap-3 text-xs">
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">{t("tradeMonitor.open")}</div>
          <div className="text-blue-400 font-semibold tabular-nums">{open}</div>
        </div>
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">{t("tradeMonitor.closed")}</div>
          <div className="text-gray-200 font-semibold tabular-nums">{closed}</div>
        </div>
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">{t("tradeMonitor.totalPnl")}</div>
          <div className={`font-semibold tabular-nums ${totalPnl >= 0 ? "text-green-400" : "text-red-400"}`}>
            ${totalPnl.toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
}

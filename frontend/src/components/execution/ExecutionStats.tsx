import { useTranslation } from "react-i18next";

interface Props {
  signals: {
    total: number;
    approved: number;
    rejected: number;
    pending: number;
    execution_rate: number;
  };
  trades: {
    total: number;
    open: number;
    closed: number;
    tp_hit: number;
    sl_hit: number;
  };
}

export default function ExecutionStats({ signals, trades }: Props) {
  const { t } = useTranslation("execution");

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">
        {t("stats.title")}
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <div className="text-[9px] text-gray-600 uppercase tracking-wider">{t("stats.signalsTotal")}</div>
          <div className="text-lg font-semibold tabular-nums text-gray-200">{signals.total}</div>
        </div>
        <div>
          <div className="text-[9px] text-gray-600 uppercase tracking-wider">{t("stats.executionRate")}</div>
          <div className="text-lg font-semibold tabular-nums text-green-400">{signals.execution_rate}%</div>
        </div>
        <div>
          <div className="text-[9px] text-gray-600 uppercase tracking-wider">{t("stats.approved")}</div>
          <div className="text-lg font-semibold tabular-nums text-green-400">{signals.approved}</div>
        </div>
        <div>
          <div className="text-[9px] text-gray-600 uppercase tracking-wider">{t("stats.rejected")}</div>
          <div className="text-lg font-semibold tabular-nums text-red-400">{signals.rejected}</div>
        </div>
        <div>
          <div className="text-[9px] text-gray-600 uppercase tracking-wider">{t("stats.tradesTotal")}</div>
          <div className="text-lg font-semibold tabular-nums text-gray-200">{trades.total}</div>
        </div>
        <div>
          <div className="text-[9px] text-gray-600 uppercase tracking-wider">{t("stats.open")}</div>
          <div className="text-lg font-semibold tabular-nums text-blue-400">{trades.open}</div>
        </div>
        <div>
          <div className="text-[9px] text-gray-600 uppercase tracking-wider">{t("stats.tpHit")}</div>
          <div className="text-lg font-semibold tabular-nums text-green-400">{trades.tp_hit}</div>
        </div>
        <div>
          <div className="text-[9px] text-gray-600 uppercase tracking-wider">{t("stats.slHit")}</div>
          <div className="text-lg font-semibold tabular-nums text-red-400">{trades.sl_hit}</div>
        </div>
      </div>
    </div>
  );
}

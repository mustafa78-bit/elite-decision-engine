import { useTranslation } from "react-i18next";

import ConfidenceBadge from "./ConfidenceBadge";

interface SignalRow {
  id: number;
  symbol: string;
  side: string;
  timeframe: string;
  price: number | null;
  confidence: number;
  decision: string;
  final_score: number;
  status: string;
  created_at: string | null;
}

interface Props {
  signals: SignalRow[];
}

export default function LiveSignalTable({ signals }: Props) {
  const { t } = useTranslation("signals");

  if (signals.length === 0) {
    return (
      <div className="text-gray-600 text-xs p-4 border border-dashed border-gray-800 rounded text-center">
        {t("liveSignalTable.noSignals")}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs text-gray-300 border-collapse">
        <thead>
          <tr className="text-[10px] uppercase text-gray-500 border-b border-gray-800">
            <th className="text-left px-2 py-1.5 font-medium">#</th>
            <th className="text-left px-2 py-1.5 font-medium">{t("liveSignalTable.columns.symbol")}</th>
            <th className="text-left px-2 py-1.5 font-medium">{t("liveSignalTable.columns.side")}</th>
            <th className="text-right px-2 py-1.5 font-medium">{t("liveSignalTable.columns.price")}</th>
            <th className="text-left px-2 py-1.5 font-medium">{t("liveSignalTable.columns.decision")}</th>
            <th className="text-right px-2 py-1.5 font-medium">{t("liveSignalTable.columns.score")}</th>
            <th className="text-left px-2 py-1.5 font-medium">{t("liveSignalTable.columns.status")}</th>
            <th className="text-right px-2 py-1.5 font-medium">{t("liveSignalTable.columns.time")}</th>
          </tr>
        </thead>
        <tbody>
          {signals.map((s, i) => (
            <tr
              key={s.id}
              className="border-b border-gray-900 hover:bg-gray-900/60 transition-colors"
            >
              <td className="px-2 py-1.5 text-gray-500 tabular-nums">{signals.length - i}</td>
              <td className="px-2 py-1.5 font-medium text-gray-100">{s.symbol}</td>
              <td className="px-2 py-1.5">
                <span className={s.side === "LONG" ? "text-green-400" : "text-red-400"}>
                  {s.side}
                </span>
              </td>
              <td className="px-2 py-1.5 text-right tabular-nums">
                {s.price != null ? s.price.toFixed(2) : "—"}
              </td>
              <td className="px-2 py-1.5">
                <ConfidenceBadge confidence={s.confidence} decision={s.decision} />
              </td>
              <td className="px-2 py-1.5 text-right tabular-nums">
                <span className={s.final_score >= 0.8 ? "text-green-400" : s.final_score >= 0.5 ? "text-yellow-400" : "text-red-400"}>
                  {(s.final_score * 100).toFixed(0)}%
                </span>
              </td>
              <td className="px-2 py-1.5">
                <span className="text-gray-500">{s.status}</span>
              </td>
              <td className="px-2 py-1.5 text-right tabular-nums text-gray-500">
                {s.created_at ? new Date(s.created_at).toLocaleTimeString() : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

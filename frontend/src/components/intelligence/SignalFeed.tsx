import { useTranslation } from "react-i18next";

interface Props {
  total: number;
  open: number;
  approved: number;
  rejected: number;
}

export default function SignalFeed({ total, open, approved, rejected }: Props) {
  const { t } = useTranslation("intelligence");

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">{t("signalFeed.title")}</h3>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">{t("signalFeed.total")}</div>
          <div className="text-gray-200 font-semibold tabular-nums">{total}</div>
        </div>
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">{t("signalFeed.open")}</div>
          <div className="text-yellow-400 font-semibold tabular-nums">{open}</div>
        </div>
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">{t("signalFeed.approved")}</div>
          <div className="text-green-400 font-semibold tabular-nums">{approved}</div>
        </div>
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">{t("signalFeed.rejected")}</div>
          <div className="text-red-400 font-semibold tabular-nums">{rejected}</div>
        </div>
      </div>
    </div>
  );
}

import { useTranslation } from "react-i18next";

interface Props {
  approved: number;
  rejected: number;
  pending: number;
}

export default function ExecutionTimeline({ approved, rejected, pending }: Props) {
  const { t } = useTranslation("execution");
  const total = approved + rejected + pending;
  const approvedPct = total > 0 ? (approved / total) * 100 : 0;
  const rejectedPct = total > 0 ? (rejected / total) * 100 : 0;
  const pendingPct = total > 0 ? (pending / total) * 100 : 0;

  if (total === 0) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded p-4">
        <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">{t("timeline.title")}</h3>
        <p className="text-gray-600 text-xs text-center py-4">{t("timeline.noData")}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">{t("timeline.title")}</h3>
      <div className="h-6 bg-gray-950 rounded-full overflow-hidden flex">
        <div className="bg-green-600 h-full transition-all" style={{ width: `${approvedPct}%` }} title={t("timeline.approvedTitle", { count: approved })} />
        <div className="bg-red-600 h-full transition-all" style={{ width: `${rejectedPct}%` }} title={t("timeline.rejectedTitle", { count: rejected })} />
        <div className="bg-yellow-600 h-full transition-all" style={{ width: `${pendingPct}%` }} title={t("timeline.pendingTitle", { count: pending })} />
      </div>
      <div className="flex gap-4 mt-2 text-[10px]">
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-green-600" />
          <span className="text-gray-400">{t("timeline.approvedLabel", { count: approved })}</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-red-600" />
          <span className="text-gray-400">{t("timeline.rejectedLabel", { count: rejected })}</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-yellow-600" />
          <span className="text-gray-400">{t("timeline.pendingLabel", { count: pending })}</span>
        </div>
      </div>
    </div>
  );
}

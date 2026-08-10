import { useTranslation } from "react-i18next";

import type { RegimeData } from "../../api/regime";

interface Props {
  data: RegimeData;
}

const TREND_COLORS: Record<string, string> = {
  BULLISH: "text-green-400",
  BEARISH: "text-red-400",
  NEUTRAL: "text-yellow-400",
};

const REGIME_COLORS: Record<string, string> = {
  TREND: "text-green-400",
  DOWNTREND: "text-red-400",
  RANGE: "text-yellow-400",
  DEAD: "text-gray-500",
};

const VOL_COLORS: Record<string, string> = {
  LOW: "text-blue-400",
  NORMAL: "text-gray-300",
  HIGH: "text-red-400",
};

export default function RegimePanel({ data }: Props) {
  const { t } = useTranslation("regime");
  const regimeLabel = t(`regimeValues.${data.regime}`, { defaultValue: data.regime });
  const trendLabel = t(`trendValues.${data.trend}`, { defaultValue: data.trend });
  const volLabel = t(`volatilityValues.${data.volatility_state}`, { defaultValue: data.volatility_state });

  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-3">
        {t("regimePanel.title")}
      </h3>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">{t("regimePanel.regime")}</div>
          <div className={`font-semibold ${REGIME_COLORS[data.regime] || "text-gray-200"}`}>
            {regimeLabel}
          </div>
        </div>
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">{t("regimePanel.trend")}</div>
          <div className={`font-semibold ${TREND_COLORS[data.trend] || "text-gray-200"}`}>
            {trendLabel}
          </div>
        </div>
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">{t("regimePanel.volatility")}</div>
          <div className={`font-semibold ${VOL_COLORS[data.volatility_state] || "text-gray-200"}`}>
            {volLabel} ({(data.volatility * 100).toFixed(2)}%)
          </div>
        </div>
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">{t("regimePanel.btcHealth")}</div>
          <div className="text-gray-200 font-semibold tabular-nums">
            {(data.btc_health * 100).toFixed(0)}%
          </div>
        </div>
        <div>
          <div className="text-gray-500 text-[9px] uppercase tracking-wider">{t("regimePanel.rsi")}</div>
          <div className="text-gray-200 font-semibold tabular-nums">{data.rsi}</div>
        </div>
      </div>
      <div className="mt-3 pt-3 border-t border-gray-800 text-[10px] text-gray-600">
        <span className="text-gray-500">{t("regimePanel.ema")} </span>
        <span className="tabular-nums">20={data.ema20} 50={data.ema50} 200={data.ema200}</span>
      </div>
    </div>
  );
}

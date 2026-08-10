import { useOutletContext } from "react-router-dom";
import { useTranslation } from "react-i18next";

import ClosedTrades from "../components/ClosedTrades";
import OpenTrades from "../components/OpenTrades";
import type { TradePayload } from "../types/trade";

interface TradesContext {
  openTrades: TradePayload[];
  closedTrades: TradePayload[];
}

export default function Trades() {
  const { openTrades, closedTrades } = useOutletContext<TradesContext>();
  const { t } = useTranslation("trades");

  return (
    <div className="space-y-4">
      <section>
        <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)] mb-2">
          {t("page.openTrades")}
        </h2>
        <OpenTrades trades={openTrades} />
      </section>

      <section>
        <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)] mb-2">
          {t("page.closedTrades")}
        </h2>
        <ClosedTrades trades={closedTrades} />
      </section>
    </div>
  );
}

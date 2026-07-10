import { useOutletContext, useParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { ExplainableAIPanel } from "../components/ai/explainable-ai-panel";
import { ConfidenceBreakdown } from "../components/ai/confidence-breakdown";
import { WhaleWidget } from "../components/ai/whale-widget";
import { NewsWidget } from "../components/ai/news-widget";
import { FundingWidget } from "../components/ai/funding-widget";
import { OpenInterestWidget } from "../components/ai/open-interest-widget";
import { LiquidityWidget } from "../components/ai/liquidity-widget";
import RiskMonitor from "../components/intelligence/RiskMonitor";
import { DecisionTimeline } from "../components/ai/decision-timeline";
import type { LayoutContext } from "../components/layout/Layout";

export default function AssetDetail() {
  const { symbol } = useParams<{ symbol: string }>();
  const { latestPrice, latestIntelligence } = useOutletContext<LayoutContext>();

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <h1 className="text-sm font-semibold text-[var(--text-primary)]">{symbol ?? "Unknown"}</h1>
        {latestPrice && (
          <Badge variant={latestPrice.change_24h >= 0 ? "success" : "danger"}>
            ${latestPrice.price.toFixed(2)}
            <span className="ml-1">{latestPrice.change_24h >= 0 ? "+" : ""}{latestPrice.change_24h.toFixed(2)}%</span>
          </Badge>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Price Chart</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[400px] flex items-center justify-center text-[var(--text-muted)] text-xs font-mono">
                Chart loading...
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader><CardTitle>RSI</CardTitle></CardHeader>
              <CardContent><span className="font-mono text-lg">--</span></CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>EMA 20/50</CardTitle></CardHeader>
              <CardContent><span className="font-mono text-lg">--</span></CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Volume</CardTitle></CardHeader>
              <CardContent><span className="font-mono text-lg">--</span></CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader><CardTitle>AI Decision</CardTitle></CardHeader>
            <CardContent>
              {latestIntelligence ? (
                <ExplainableAIPanel
                  symbol={symbol}
                  prediction={latestIntelligence.decision}
                  confidence={Math.round(latestIntelligence.confidence * 100)}
                />
              ) : (
                <div className="text-[var(--text-muted)] text-xs font-mono">No decision data</div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Decision Timeline</CardTitle></CardHeader>
            <CardContent>
              <DecisionTimeline />
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <RiskMonitor openTrades={0} maxOpenTrades={10} />
          <ConfidenceBreakdown />
          <WhaleWidget />
          <NewsWidget />
          <FundingWidget />
          <OpenInterestWidget />
          <LiquidityWidget />
        </div>
      </div>
    </div>
  );
}

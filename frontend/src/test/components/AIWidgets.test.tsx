import { describe, expect, it } from "vitest";
import { render, screen } from "../test-utils";
import { WhaleWidget } from "../../components/ai/whale-widget";
import { FundingWidget } from "../../components/ai/funding-widget";
import { OpenInterestWidget } from "../../components/ai/open-interest-widget";
import { LiquidityWidget } from "../../components/ai/liquidity-widget";
import { MemoryWidget } from "../../components/ai/memory-widget";
import { DecisionTimeline } from "../../components/ai/decision-timeline";

describe("WhaleWidget", () => {
  it("shows empty state", () => {
    render(<WhaleWidget />);
    expect(screen.getByText("No whale activity detected")).toBeInTheDocument();
  });

  it("renders whale activities", () => {
    const activities = [
      { symbol: "BTC", type: "buy" as const, amount: 100, usdValue: 4_200_000, time: "2m ago", exchange: "Binance" },
    ];
    render(<WhaleWidget activities={activities} />);
    expect(screen.getByText("BTC")).toBeInTheDocument();
    expect(screen.getByText("$4.2M")).toBeInTheDocument();
  });
});

describe("FundingWidget", () => {
  it("shows empty state", () => {
    render(<FundingWidget />);
    expect(screen.getByText("No funding data available")).toBeInTheDocument();
  });

  it("renders funding rates", () => {
    const rates = [{ symbol: "BTC/USDT", rate: 0.0001, apr: 5.2, timeToSettlement: "2h", sentiment: "bullish" as const }];
    render(<FundingWidget rates={rates} />);
    expect(screen.getByText("BTC/USDT")).toBeInTheDocument();
  });
});

describe("OpenInterestWidget", () => {
  it("shows empty state", () => {
    render(<OpenInterestWidget />);
    expect(screen.getByText("No OI data available")).toBeInTheDocument();
  });
});

describe("LiquidityWidget", () => {
  it("renders symbol", () => {
    render(<LiquidityWidget />);
    expect(screen.getByText("BTC/USDT")).toBeInTheDocument();
  });
});

describe("MemoryWidget", () => {
  it("shows empty state", () => {
    render(<MemoryWidget />);
    expect(screen.getByText("No memory entries recorded")).toBeInTheDocument();
  });
});

describe("DecisionTimeline", () => {
  it("shows empty state", () => {
    render(<DecisionTimeline />);
    expect(screen.getByText("No recent decisions")).toBeInTheDocument();
  });
});

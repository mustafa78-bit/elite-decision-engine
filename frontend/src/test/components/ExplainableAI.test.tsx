import { describe, expect, it } from "vitest";
import { render, screen } from "../test-utils";
import { ExplainableAIPanel } from "../../components/ai/explainable-ai-panel";

describe("ExplainableAIPanel", () => {
  it("renders title and default symbol", () => {
    render(<ExplainableAIPanel />);
    expect(screen.getByText("Explainable AI")).toBeInTheDocument();
    expect(screen.getByText("BTC/USDT")).toBeInTheDocument();
  });

  it("shows prediction badge when passed", () => {
    render(<ExplainableAIPanel prediction="BULLISH" confidence={78} />);
    expect(screen.getByText("BULLISH 78%")).toBeInTheDocument();
  });

  it("renders factor contributions when provided", () => {
    const factors = [
      { factor: "Technical Momentum", impact: 35, direction: "positive" as const, description: "RSI > 60, MACD bullish cross" },
      { factor: "Volume Analysis", impact: 25, direction: "positive" as const, description: "Volume 2.5x above 24h average" },
    ];
    render(<ExplainableAIPanel factors={factors} />);
    expect(screen.getByText("Factor Contributions")).toBeInTheDocument();
    expect(screen.getByText("Technical Momentum")).toBeInTheDocument();
    expect(screen.getByText("Volume Analysis")).toBeInTheDocument();
  });

  it("shows pending state when no prediction given", () => {
    render(<ExplainableAIPanel />);
    expect(screen.getByText("PENDING 0%")).toBeInTheDocument();
  });
});

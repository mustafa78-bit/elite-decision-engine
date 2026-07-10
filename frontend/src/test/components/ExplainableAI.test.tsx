import { describe, expect, it } from "vitest";
import { render, screen } from "../test-utils";
import { ExplainableAIPanel } from "../../components/ai/explainable-ai-panel";

describe("ExplainableAIPanel", () => {
  it("renders title and symbol", () => {
    render(<ExplainableAIPanel />);
    expect(screen.getByText("Explainable AI")).toBeInTheDocument();
    expect(screen.getByText("BTC/USDT")).toBeInTheDocument();
  });

  it("renders factor contributions", () => {
    render(<ExplainableAIPanel />);
    expect(screen.getByText("Factor Contributions")).toBeInTheDocument();
    expect(screen.getByText("Technical Momentum")).toBeInTheDocument();
    expect(screen.getByText("Volume Analysis")).toBeInTheDocument();
  });

  it("shows prediction badge", () => {
    render(<ExplainableAIPanel />);
    expect(screen.getByText("BULLISH 78%")).toBeInTheDocument();
  });
});

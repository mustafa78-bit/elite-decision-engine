import { describe, expect, it } from "vitest";
import { render, screen } from "../test-utils";
import { KPICard } from "../../components/dashboard/KPICard";
import type { KPIDTO } from "../../types/api/widget";

const sampleKPI: KPIDTO = {
  name: "Total PnL",
  value: 2500,
  unit: "USD",
  trend: "improving",
  status: "positive",
};

describe("KPICard", () => {
  it("renders KPI name", () => {
    render(<KPICard kpi={sampleKPI} />);
    expect(screen.getByText("Total PnL")).toBeInTheDocument();
  });

  it("renders value and unit in separate spans", () => {
    render(<KPICard kpi={sampleKPI} />);
    expect(screen.getByText("USD")).toBeInTheDocument();
  });

  it("renders percentage unit correctly", () => {
    render(<KPICard kpi={{ ...sampleKPI, name: "Win Rate", value: 75, unit: "%" }} />);
    expect(screen.getByText("Win Rate")).toBeInTheDocument();
    expect(screen.getByText("%")).toBeInTheDocument();
  });
});

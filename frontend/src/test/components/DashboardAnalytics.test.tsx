import { describe, expect, it } from "vitest";
import { render, screen } from "../test-utils";
import { DashboardAnalytics } from "../../components/dashboard/dashboard-analytics";

describe("DashboardAnalytics", () => {
  it("renders compact mode", () => {
    render(<DashboardAnalytics compact />);
    expect(screen.getByText(/widgets/)).toBeInTheDocument();
  });

  it("renders full mode", () => {
    render(<DashboardAnalytics />);
    expect(screen.getByText("Dashboard Analytics")).toBeInTheDocument();
  });
});

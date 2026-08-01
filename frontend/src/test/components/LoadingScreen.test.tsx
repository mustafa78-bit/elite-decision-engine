import { describe, expect, it } from "vitest";
import { render, screen } from "../test-utils";
import { LoadingScreen } from "../../components/layout/LoadingScreen";

describe("LoadingScreen", () => {
  it("renders default message", () => {
    render(<LoadingScreen />);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders custom message", () => {
    render(<LoadingScreen message="Fetching data..." />);
    expect(screen.getByText("Fetching data...")).toBeInTheDocument();
  });
});

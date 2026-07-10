import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "../test-utils";
import { WorkspacePresets } from "../../components/workspace/workspace-presets";

describe("WorkspacePresets", () => {
  it("renders preset button", () => {
    render(<WorkspacePresets />);
    expect(screen.getByText("Presets")).toBeInTheDocument();
  });

  it("shows presets on click", async () => {
    render(<WorkspacePresets />);
    fireEvent.click(screen.getByText("Presets"));
    expect(await screen.findByText("Trading")).toBeInTheDocument();
    expect(screen.getByText("Analytics")).toBeInTheDocument();
    expect(screen.getByText("Monitoring")).toBeInTheDocument();
  });
});

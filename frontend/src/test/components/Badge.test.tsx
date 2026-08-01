import { describe, expect, it } from "vitest";
import { render, screen } from "../test-utils";
import { Badge } from "../../components/ui/badge";

describe("Badge", () => {
  it("renders children", () => {
    render(<Badge>Active</Badge>);
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("applies variant classes", () => {
    render(<Badge variant="success">Win</Badge>);
    expect(screen.getByText("Win").className).toContain("accent-green");
  });
});

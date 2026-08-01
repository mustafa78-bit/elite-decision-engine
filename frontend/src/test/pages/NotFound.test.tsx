import { describe, expect, it } from "vitest";
import { render, screen } from "../test-utils";
import NotFound from "../../pages/NotFound";

describe("NotFound", () => {
  it("renders 404 message", () => {
    render(<NotFound />);
    expect(screen.getByText("404")).toBeInTheDocument();
    expect(screen.getByText("Page not found")).toBeInTheDocument();
    expect(screen.getByText("Back to Dashboard")).toBeInTheDocument();
  });
});

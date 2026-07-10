import { describe, expect, it } from "vitest";
import { render, screen } from "../test-utils";
import { Button } from "../../components/ui/button";

describe("Button", () => {
  it("renders children", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("applies variant classes", () => {
    render(<Button variant="danger">Delete</Button>);
    const btn = screen.getByText("Delete");
    expect(btn.className).toContain("bg-red-900");
  });

  it("disables correctly", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByText("Disabled")).toBeDisabled();
  });
});

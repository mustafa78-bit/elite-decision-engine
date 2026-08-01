import { describe, expect, it } from "vitest";
import { render } from "../test-utils";
import { Skeleton } from "../../components/ui/skeleton";

describe("Skeleton", () => {
  it("renders with animate-pulse class", () => {
    const { container } = render(<Skeleton className="h-10 w-full" />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain("animate-pulse");
    expect(el.className).toContain("bg-elevated");
  });
});

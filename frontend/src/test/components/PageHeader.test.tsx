import { describe, expect, it } from "vitest";
import { render, screen } from "../test-utils";
import { PageHeader } from "../../components/ui/PageHeader";

describe("PageHeader", () => {
  it("renders title and subtitle", () => {
    render(<PageHeader title="Overview" subtitle="Systems status" />);
    expect(screen.getByText("Overview")).toBeInTheDocument();
    expect(screen.getByText("Systems status")).toBeInTheDocument();
  });
});

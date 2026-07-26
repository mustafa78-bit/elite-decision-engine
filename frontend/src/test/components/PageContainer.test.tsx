import { describe, expect, it } from "vitest";
import { render, screen } from "../test-utils";
import { PageContainer } from "../../components/ui/PageContainer";

describe("PageContainer", () => {
  it("renders children", () => {
    render(
      <PageContainer>
        <div>Content</div>
      </PageContainer>
    );
    expect(screen.getByText("Content")).toBeInTheDocument();
  });
});

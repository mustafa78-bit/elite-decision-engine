import { describe, expect, it, beforeEach } from "vitest";
import { render, screen } from "../test-utils";
import { GlobalSearch } from "../../components/workspace/global-search";
import { useUIStore } from "../../stores/ui-store";

describe("GlobalSearch", () => {
  beforeEach(() => {
    useUIStore.setState({ globalSearchOpen: true });
  });

  it("renders search input", () => {
    render(<GlobalSearch />);
    expect(screen.getByPlaceholderText("Search pages, symbols, actions...")).toBeInTheDocument();
  });

  it("renders categories", () => {
    render(<GlobalSearch />);
    expect(screen.getByText("Pages")).toBeInTheDocument();
    expect(screen.getByText("Actions")).toBeInTheDocument();
    expect(screen.getByText("Symbols")).toBeInTheDocument();
  });

  it("shows navigation hints", () => {
    render(<GlobalSearch />);
    expect(screen.getByText("↑↓ Navigate")).toBeInTheDocument();
    expect(screen.getByText("↵ Open")).toBeInTheDocument();
    expect(screen.getByText("Esc Close")).toBeInTheDocument();
  });
});

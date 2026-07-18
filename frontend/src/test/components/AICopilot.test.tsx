import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "../test-utils";
import { AIChat } from "../../components/ai/ai-chat";

describe("AIChat Copilot component", () => {
  it("renders the chat panel with welcome message and default suggestions", () => {
    render(<AIChat />);

    // Renders the component header
    expect(screen.getByText("Elite AI Copilot")).toBeInTheDocument();
    expect(screen.getByText("Explainable Mode Active")).toBeInTheDocument();

    // Renders the welcome message content
    expect(screen.getByText(/Welcome to Elite Decision Assistant!/i)).toBeInTheDocument();

    // Renders default contextual suggestions
    expect(screen.getByText("Why should I buy BTC?")).toBeInTheDocument();
    expect(screen.getByText("What are the biggest portfolio risks?")).toBeInTheDocument();
  });

  it("handles sending a message and rendering the backend response", async () => {
    const mockResponse = {
      reply: "### AI Analysis: Why Buy BTC?\n- **Current Price**: `$43,000.00`\n- **Overall Score**: `92.0`\n\n**Conclusion**: STRONG APPROVE.",
      suggestions: ["What changed in the last hour?", "Show me the best opportunities today."],
      links: [{ label: "Portfolio Dashboard", path: "/portfolio" }],
      metrics: { score: 92.0, price: 43000.0 }
    };

    // Mock global fetch for API calls
    const fetchSpy = vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockResponse),
        })
      )
    );

    render(<AIChat />);

    // Click a suggestion button to send a message
    const suggestionBtn = screen.getByText("Why should I buy BTC?");
    fireEvent.click(suggestionBtn);

    // Verify loading message displays
    expect(screen.getByText("Analyzing platform metrics")).toBeInTheDocument();

    // Wait for mock API response to populate and render on screen
    await waitFor(() => {
      expect(screen.getByText("AI Analysis: Why Buy BTC?")).toBeInTheDocument();
      expect(screen.getByText("Portfolio Dashboard")).toBeInTheDocument();
      expect(screen.getByText("What changed in the last hour?")).toBeInTheDocument();
    });

    vi.unstubAllGlobals();
  });

  it("gracefully handles API network failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() =>
        Promise.resolve({
          ok: false,
          status: 500,
          statusText: "Internal Server Error",
        })
      )
    );

    render(<AIChat />);

    const suggestionBtn = screen.getByText("What are the biggest portfolio risks?");
    fireEvent.click(suggestionBtn);

    await waitFor(() => {
      expect(screen.getByText(/API Connection Error/i)).toBeInTheDocument();
    });

    vi.unstubAllGlobals();
  });
});

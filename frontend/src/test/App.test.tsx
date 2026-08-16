import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import { AppRoutes } from "../App";
import { apiFetch } from "../api/client";

// AppRoutes calls useAuth() directly (its own <AuthProvider> wrapping
// happens one level up, in the default-exported App()) -- mock the hook
// so AppRoutes sees an authenticated session without going through real
// login/localStorage plumbing.
vi.mock("../components/auth/AuthProvider", () => ({
  useAuth: () => ({
    user: "trader",
    token: "fake-token",
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

type MessageHandler = (data: unknown) => void;
let capturedOnMessage: MessageHandler | undefined;

vi.mock("../websocket/client", () => ({
  connectTradesSocket: (onMessage: MessageHandler, onStatus?: (s: string) => void) => {
    capturedOnMessage = onMessage;
    onStatus?.("CONNECTED");
    return { close: vi.fn() } as unknown as WebSocket;
  },
}));

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, apiFetch: vi.fn() };
});

describe("AppRoutes open trades hydration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    capturedOnMessage = undefined;
    window.history.pushState({}, "", "/trades");
  });

  it("hydrates openTrades/closedTrades from /paper/positions on load, not just from live websocket events", async () => {
    // Distinctive symbols (not BTC/ETH) so this assertion can't accidentally
    // match an unrelated default-symbol display elsewhere in the layout.
    vi.mocked(apiFetch).mockResolvedValue({
      positions: [
        { id: 1, symbol: "DOGE", side: "LONG", entry: 100, stop: 90, tp1: 120, tp2: null, status: "OPEN", pnl: 0, exit_price: null, close_reason: null },
        { id: 2, symbol: "SOL", side: "SHORT", entry: 50, stop: 55, tp1: 40, tp2: null, status: "CLOSED", pnl: 10, exit_price: 40, close_reason: "TP" },
      ],
    });

    render(<AppRoutes />);

    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith("/paper/positions?limit=200");
    });

    // The OPEN position ends up in the open-trades table...
    await waitFor(() => {
      expect(screen.getByText("DOGE")).toBeInTheDocument();
    });
    // ...and the non-OPEN one in the closed-trades table -- neither needed
    // a live TRADE_OPENED/TRADE_CLOSED websocket event to appear.
    expect(screen.getByText("SOL")).toBeInTheDocument();
  });

  it("does not duplicate a trade already hydrated when its own TRADE_OPENED event later arrives", async () => {
    vi.mocked(apiFetch).mockResolvedValue({
      positions: [
        { id: 1, symbol: "DOGE", side: "LONG", entry: 100, stop: 90, tp1: 120, tp2: null, status: "OPEN", pnl: 0, exit_price: null, close_reason: null },
      ],
    });

    render(<AppRoutes />);

    await waitFor(() => {
      expect(capturedOnMessage).toBeDefined();
    });
    await waitFor(() => {
      expect(screen.getAllByText("DOGE")).toHaveLength(1);
    });

    capturedOnMessage!({
      event: "TRADE_OPENED",
      timestamp: new Date().toISOString(),
      payload: { trade_id: 1, symbol: "DOGE", side: "LONG", entry: 100, status: "OPEN" },
    });

    await waitFor(() => {
      expect(screen.getAllByText("DOGE")).toHaveLength(1);
    });
  });
});

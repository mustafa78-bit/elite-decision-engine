import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider, Outlet } from "react-router-dom";
import Profile from "../../pages/Profile";
import { fetchCurrentUser } from "../../api/users";
import { fetchPreferences } from "../../api/preferences";
import type { LayoutContext } from "../../components/layout/Layout";

vi.mock("../../components/auth/AuthProvider", () => ({
  useAuth: () => ({
    user: "testuser",
    token: "fake-token",
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

vi.mock("../../api/users", () => ({ fetchCurrentUser: vi.fn() }));
vi.mock("../../api/preferences", () => ({ fetchPreferences: vi.fn() }));

function renderProfile(context: Partial<LayoutContext> = {}) {
  const fullContext: LayoutContext = {
    notifications: [],
    openTrades: [],
    closedTrades: [],
    latestMarket: null,
    latestSignal: null,
    latestRiskWs: null,
    latestPrice: null,
    latestCandle: null,
    latestVolume: null,
    ...context,
  };
  const router = createMemoryRouter(
    [
      {
        path: "/",
        element: <Outlet context={fullContext} />,
        children: [{ path: "profile", element: <Profile /> }],
      },
    ],
    { initialEntries: ["/profile"] },
  );
  return render(<RouterProvider router={router} />);
}

describe("Profile", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows the real member-since date once /users/me loads, not a hardcoded 'unavailable'", async () => {
    vi.mocked(fetchCurrentUser).mockResolvedValue({
      id: 1, username: "testuser", email: "t@example.com", created_at: "2026-01-15T00:00:00Z",
    });
    vi.mocked(fetchPreferences).mockResolvedValue({
      theme: "dark", layout_config: {}, notification_preferences: {},
    });

    renderProfile();

    await waitFor(() => {
      expect(screen.getByText(/January 15, 2026/)).toBeInTheDocument();
    });
  });

  it("shows real per-event notification preference on/off state from /preferences", async () => {
    vi.mocked(fetchCurrentUser).mockResolvedValue({
      id: 1, username: "testuser", email: "t@example.com", created_at: null,
    });
    vi.mocked(fetchPreferences).mockResolvedValue({
      theme: "dark",
      layout_config: {},
      notification_preferences: { trade_opened: true, trade_closed: false, system_alert: true },
    });

    renderProfile();

    await waitFor(() => {
      expect(screen.getAllByText("On")).toHaveLength(2);
    });
    expect(screen.getByText("Off")).toBeInTheDocument();
  });

  it("renders recent trade activity from live LayoutContext notifications", async () => {
    vi.mocked(fetchCurrentUser).mockResolvedValue({
      id: 1, username: "testuser", email: "t@example.com", created_at: null,
    });
    vi.mocked(fetchPreferences).mockResolvedValue({
      theme: "dark", layout_config: {}, notification_preferences: {},
    });

    renderProfile({
      notifications: [
        {
          event: "TRADE_OPENED",
          timestamp: "2026-01-15T10:00:00Z",
          payload: { symbol: "BTCUSDT", side: "LONG", entry: 60000, status: "OPEN" },
        },
      ],
    });

    await waitFor(() => {
      expect(screen.getByText(/BTCUSDT LONG/)).toBeInTheDocument();
    });
  });

  it("shows an empty state when there is no recent activity", async () => {
    vi.mocked(fetchCurrentUser).mockResolvedValue({
      id: 1, username: "testuser", email: "t@example.com", created_at: null,
    });
    vi.mocked(fetchPreferences).mockResolvedValue({
      theme: "dark", layout_config: {}, notification_preferences: {},
    });

    renderProfile();

    await waitFor(() => {
      expect(screen.getByText("No activity yet")).toBeInTheDocument();
    });
  });
});

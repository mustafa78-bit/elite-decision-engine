import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { AuthProvider, useAuth } from "../../components/auth/AuthProvider";
import { setUnauthorizedHandler } from "../../api/client";

function TestConsumer() {
  const { isAuthenticated, token } = useAuth();
  return (
    <div>
      <span data-testid="authed">{String(isAuthenticated)}</span>
      <span data-testid="token">{token ?? ""}</span>
    </div>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    setUnauthorizedHandler(null);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    setUnauthorizedHandler(null);
  });

  it("proactive refresh fires on the interval and updates the stored token", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    localStorage.setItem("auth_token", "old-token");

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ success: true, token: "new-token" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    expect(screen.getByTestId("token").textContent).toBe("old-token");

    // Advance past the 45-minute proactive-refresh interval.
    await vi.advanceTimersByTimeAsync(45 * 60 * 1000 + 1000);

    await waitFor(() => {
      expect(screen.getByTestId("token").textContent).toBe("new-token");
      expect(localStorage.getItem("auth_token")).toBe("new-token");
    });

    const refreshCall = fetchMock.mock.calls.find((call: unknown[]) =>
      String(call[0]).includes("/auth/refresh"),
    );
    expect(refreshCall).toBeDefined();
  });

  it("does not schedule a refresh when there is no token", () => {
    vi.useFakeTimers();
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    expect(screen.getByTestId("authed").textContent).toBe("false");
    vi.advanceTimersByTime(60 * 60 * 1000);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("registers a 401 handler on mount that logs out and clears storage", async () => {
    localStorage.setItem("auth_token", "some-token");
    localStorage.setItem("auth_user", "someone");

    let capturedHandler: (() => void) | null = null;
    const clientModule = await import("../../api/client");
    vi.spyOn(clientModule, "setUnauthorizedHandler").mockImplementation((fn) => {
      capturedHandler = fn;
    });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("authed").textContent).toBe("true");
    });
    expect(capturedHandler).not.toBeNull();

    // Simulate a 401 arriving elsewhere in the app -- client.ts would call
    // this handler; verify it does the real logout cleanup.
    capturedHandler!();

    expect(localStorage.getItem("auth_token")).toBeNull();
    expect(localStorage.getItem("auth_user")).toBeNull();

    vi.restoreAllMocks();
  });
});

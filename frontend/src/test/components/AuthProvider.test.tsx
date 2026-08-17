import { useEffect } from "react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
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

  it("proactive refresh fires on the interval, rotates both tokens", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    localStorage.setItem("auth_token", "old-token");
    localStorage.setItem("auth_refresh_token", "old-refresh-token");

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ success: true, token: "new-token", refresh_token: "new-refresh-token" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    expect(screen.getByTestId("token").textContent).toBe("old-token");

    // Advance past the 15-minute proactive-refresh interval.
    await vi.advanceTimersByTimeAsync(15 * 60 * 1000 + 1000);

    await waitFor(() => {
      expect(screen.getByTestId("token").textContent).toBe("new-token");
      expect(localStorage.getItem("auth_token")).toBe("new-token");
      expect(localStorage.getItem("auth_refresh_token")).toBe("new-refresh-token");
    });

    const refreshCall = fetchMock.mock.calls.find((call: unknown[]) =>
      String(call[0]).includes("/auth/refresh"),
    );
    expect(refreshCall).toBeDefined();
    const body = JSON.parse((refreshCall![1] as RequestInit).body as string);
    expect(body).toEqual({ refresh_token: "old-refresh-token" });
  });

  it("does not schedule a refresh when there is a token but no refresh token", () => {
    vi.useFakeTimers();
    localStorage.setItem("auth_token", "some-token");
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    vi.advanceTimersByTime(60 * 60 * 1000);
    expect(fetchMock).not.toHaveBeenCalled();
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

  it("login() writes auth_token to localStorage before isAuthenticated-gated children mount, so their own mount-time requests are never sent without it", async () => {
    // Regression: reproduced live -- a fresh login immediately self-logged-
    // out. login() only called setToken(); the actual localStorage write
    // happened in a separate useEffect keyed on [token], which fires AFTER
    // (not before) newly-mounted descendants' own mount effects in the
    // same commit (children-before-ancestor is React's real effect order).
    // Any component that only renders once isAuthenticated flips true
    // (exactly how AuthGuard gates Layout in the real app) and fires an
    // apiFetch() on mount read a stale/empty auth_token, got a 401, and
    // the global 401 handler immediately logged the user back out.
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ success: true, token: "fresh-token", refresh_token: "fresh-refresh-token" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    let capturedLogin: ((u: string, p: string) => Promise<void>) | null = null;
    const tokenSeenOnMount: (string | null)[] = [];

    function ChildThatReadsLocalStorageOnMount() {
      useEffect(() => {
        tokenSeenOnMount.push(localStorage.getItem("auth_token"));
      }, []);
      return null;
    }

    function Consumer() {
      const { login, isAuthenticated } = useAuth();
      capturedLogin = login;
      // Mirrors the real app: AuthGuard only mounts Layout (and everything
      // under it) once isAuthenticated is true.
      return isAuthenticated ? <ChildThatReadsLocalStorageOnMount /> : null;
    }

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );

    await act(async () => {
      await capturedLogin!("someone", "pw");
    });

    expect(tokenSeenOnMount).toEqual(["fresh-token"]);
  });

  it("logout revokes the refresh token server-side and clears it locally", async () => {
    localStorage.setItem("auth_token", "some-token");
    localStorage.setItem("auth_refresh_token", "some-refresh-token");
    localStorage.setItem("auth_user", "someone");

    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({ success: true }) });
    vi.stubGlobal("fetch", fetchMock);

    let capturedLogout: (() => void) | null = null;
    function Consumer() {
      const { logout } = useAuth();
      capturedLogout = logout;
      return null;
    }

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );

    capturedLogout!();

    expect(localStorage.getItem("auth_token")).toBeNull();
    expect(localStorage.getItem("auth_refresh_token")).toBeNull();

    await waitFor(() => {
      const logoutCall = fetchMock.mock.calls.find((call: unknown[]) => String(call[0]).includes("/auth/logout"));
      expect(logoutCall).toBeDefined();
      const body = JSON.parse((logoutCall![1] as RequestInit).body as string);
      expect(body).toEqual({ refresh_token: "some-refresh-token" });
    });
  });
});

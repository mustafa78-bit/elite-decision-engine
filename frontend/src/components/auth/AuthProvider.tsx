import { createContext, useContext, useState, useEffect, useCallback, useRef, type ReactNode } from "react";
import i18n from "../../i18n";
import { apiFetch, setUnauthorizedHandler } from "../../api/client";
import { addGlobalToast } from "../layout/toast-provider";

interface AuthState {
  user: string | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

// Renew well under the access token's now-short 30-minute expiry (see
// auth/jwt.py::ACCESS_TOKEN_EXPIRE_MINUTES) so an actively-open tab never
// actually reaches it. This is a single-user/trial-scale app -- a plain
// interval is proportionate, no need for a background job queue.
const PROACTIVE_REFRESH_INTERVAL_MS = 15 * 60 * 1000; // 15 minutes

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("auth_token"));
  const [user, setUser] = useState<string | null>(() => localStorage.getItem("auth_user"));
  const [isLoading, setIsLoading] = useState(false);
  // logout() is referenced by the 401 handler registered once on mount --
  // a ref avoids re-registering (and dropping) that handler on every render.
  const logoutRef = useRef<() => void>(() => {});

  useEffect(() => {
    if (token) {
      localStorage.setItem("auth_token", token);
    } else {
      localStorage.removeItem("auth_token");
    }
  }, [token]);

  const login = useCallback(async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await apiFetch<{ success: boolean; token?: string; refresh_token?: string; error?: string }>(
        "/auth/login",
        { method: "POST", body: JSON.stringify({ username, password }) },
      );
      if (!res.success || !res.token || !res.refresh_token) {
        throw new Error(res.error || "Login failed");
      }
      setToken(res.token);
      localStorage.setItem("auth_refresh_token", res.refresh_token);
      setUser(username);
      localStorage.setItem("auth_user", username);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    // Best-effort: revoke the refresh token server-side so a copy of it
    // (if one leaked) can't be used later. Never block clearing local
    // state on this -- the user is logged out locally regardless of
    // whether the network call itself succeeds.
    const refreshToken = localStorage.getItem("auth_refresh_token");
    if (refreshToken) {
      apiFetch("/auth/logout", {
        method: "POST",
        body: JSON.stringify({ refresh_token: refreshToken }),
      }).catch(() => {});
    }
    setToken(null);
    setUser(null);
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_refresh_token");
    localStorage.removeItem("auth_user");
  }, []);

  useEffect(() => {
    logoutRef.current = logout;
  }, [logout]);

  // Reactive safety net: apiFetch/apiFetchText are plain functions and can't
  // reach logout()/navigation directly, so they call this registered handler
  // on any 401. Covers the case proactive refresh below didn't (laptop
  // asleep past the interval, tab was closed and reopened with a stale
  // token, etc).
  useEffect(() => {
    setUnauthorizedHandler(() => {
      logoutRef.current();
      addGlobalToast(i18n.t("loginPage:sessionExpired"), "error");
      window.location.href = "/login";
    });
    return () => setUnauthorizedHandler(null);
  }, []);

  // Proactive refresh: while a tab is open and authenticated, periodically
  // renew the token before it actually expires. connectTradesSocket()
  // (App.tsx) already re-reads auth_token from localStorage fresh on every
  // reconnect attempt, so updating localStorage here is sufficient to reach
  // it too -- no separate websocket-side refresh wiring needed.
  useEffect(() => {
    if (!token) return;

    const interval = setInterval(async () => {
      const currentRefreshToken = localStorage.getItem("auth_refresh_token");
      if (!currentRefreshToken) return;
      try {
        // Rotation: the server always issues a brand-new refresh_token
        // alongside the new access token and revokes the one just
        // presented -- both must be persisted, or the next refresh
        // attempt will present an already-revoked token and trip the
        // server's reuse-detection (see auth/service.py::refresh_session).
        const res = await apiFetch<{ success: boolean; token?: string; refresh_token?: string }>(
          "/auth/refresh",
          { method: "POST", body: JSON.stringify({ refresh_token: currentRefreshToken }) },
        );
        if (res.success && res.token && res.refresh_token) {
          setToken(res.token);
          localStorage.setItem("auth_refresh_token", res.refresh_token);
        }
      } catch {
        // A refresh failure here isn't fatal on its own -- if the token
        // has genuinely expired, the next real API call's 401 triggers the
        // reactive safety net above. Nothing to do but wait for that.
      }
    }, PROACTIVE_REFRESH_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [token]);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

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

// Renew well under the 24h access-token expiry so an actively-open tab never
// actually reaches it. This is a single-user/trial-scale app -- a plain
// interval is proportionate, no need for a background job queue.
const PROACTIVE_REFRESH_INTERVAL_MS = 45 * 60 * 1000; // 45 minutes

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
      const res = await apiFetch<{ success: boolean; token?: string; error?: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      if (!res.success || !res.token) {
        throw new Error(res.error || "Login failed");
      }
      setToken(res.token);
      setUser(username);
      localStorage.setItem("auth_user", username);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("auth_token");
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
      const currentToken = localStorage.getItem("auth_token");
      if (!currentToken) return;
      try {
        const res = await apiFetch<{ success: boolean; token?: string }>("/auth/refresh", {
          method: "POST",
        });
        if (res.success && res.token) {
          setToken(res.token);
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

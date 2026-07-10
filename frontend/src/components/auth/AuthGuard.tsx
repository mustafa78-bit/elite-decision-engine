import { Navigate } from "react-router-dom";
import type { ReactNode } from "react";

interface AuthGuardProps {
  children: ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
  const token = localStorage.getItem("auth_token");
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export function useAuth() {
  const token = localStorage.getItem("auth_token");
  const isAuthenticated = !!token;
  return {
    isAuthenticated,
    login: (t: string) => localStorage.setItem("auth_token", t),
    logout: () => localStorage.removeItem("auth_token"),
  };
}

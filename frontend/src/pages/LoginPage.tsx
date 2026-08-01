import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { addGlobalToast } from "../components/layout/toast-provider";
import { useAuth } from "../components/auth/AuthProvider";

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await login(username, password);
      addGlobalToast("Logged in successfully", "success");
      navigate("/dashboard");
    } catch {
      addGlobalToast("Invalid credentials", "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-screen flex items-center justify-center bg-[var(--bg-elevated)]">
      <form
        onSubmit={handleSubmit}
        className="border border-[var(--border-subtle)] rounded p-6 w-full max-w-sm space-y-4"
      >
        <div>
          <h1 className="text-sm font-semibold tracking-wide text-[var(--text-primary)]">
            Elite Terminal
          </h1>
          <p className="text-[9px] text-[var(--text-muted)] uppercase tracking-widest mt-1">
            Sign in to continue
          </p>
        </div>

        <Input
          id="username"
          label="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="admin"
          autoComplete="username"
        />

        <Input
          id="password"
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          autoComplete="current-password"
        />

        <Button type="submit" disabled={loading} className="w-full">
          {loading ? "Signing in..." : "Sign In"}
        </Button>
      </form>
    </div>
  );
}

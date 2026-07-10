import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { addGlobalToast } from "../components/layout/ToastProvider";
import { apiFetch } from "../api/client";

export default function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await apiFetch<{ token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      localStorage.setItem("auth_token", res.token);
      addGlobalToast("Logged in successfully", "success");
      navigate("/dashboard");
    } catch {
      addGlobalToast("Invalid credentials", "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-screen flex items-center justify-center bg-gray-950">
      <form
        onSubmit={handleSubmit}
        className="border border-gray-800 rounded p-6 w-full max-w-sm space-y-4"
      >
        <div>
          <h1 className="text-sm font-semibold tracking-wide text-gray-100">
            Elite Terminal
          </h1>
          <p className="text-[9px] text-gray-600 uppercase tracking-widest mt-1">
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

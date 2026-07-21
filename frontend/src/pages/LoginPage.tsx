import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../components/auth/AuthProvider";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { addGlobalToast } from "../components/layout/toast-provider";

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      addGlobalToast("Please enter both username and password", "error");
      return;
    }

    setLoading(true);
    try {
      await login(username, password);
      addGlobalToast("Logged in successfully", "success");
      navigate("/overview");
    } catch {
      addGlobalToast("Invalid credentials", "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="h-screen flex items-center justify-center bg-slate-50">
      <form
        onSubmit={handleSubmit}
        className="bg-white border border-slate-200 rounded-xl p-8 w-full max-w-sm space-y-6 shadow-sm"
      >
        <div className="text-center pb-2 border-b border-slate-100">
          <div className="w-10 h-10 rounded bg-blue-600 flex items-center justify-center text-white font-extrabold text-lg mx-auto shadow-sm">
            Φ
          </div>
          <h1 className="text-lg font-bold text-slate-900 tracking-tight mt-3">
            Elite Decision Intelligence
          </h1>
          <p className="text-[10px] text-blue-600 font-bold uppercase tracking-widest mt-1">
            Institutional Desktop Core
          </p>
        </div>

        <div className="space-y-4">
          <Input
            id="username"
            label="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="admin"
            autoComplete="username"
            required
            className="bg-white text-slate-900 border-slate-200"
          />

          <Input
            id="password"
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            autoComplete="current-password"
            required
            className="bg-white text-slate-900 border-slate-200"
          />
        </div>

        <Button
          type="submit"
          variant="primary"
          disabled={loading}
          className="w-full h-10 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm rounded-lg cursor-pointer transition-colors shadow-sm"
        >
          {loading ? "Signing in..." : "Sign In"}
        </Button>
      </form>
    </div>
  );
}

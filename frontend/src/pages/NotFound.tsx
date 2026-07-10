import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="h-full flex flex-col items-center justify-center gap-4">
      <div className="text-4xl font-mono text-gray-700">404</div>
      <p className="text-xs text-gray-500 font-mono uppercase tracking-widest">
        Page not found
      </p>
      <Button variant="outline" onClick={() => navigate("/dashboard")}>
        Back to Dashboard
      </Button>
    </div>
  );
}

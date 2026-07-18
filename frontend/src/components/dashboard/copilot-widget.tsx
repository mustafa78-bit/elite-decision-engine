import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "../ui/card";

interface CopilotCommand {
  label: string;
  command: string;
  description: string;
}

const fastCommands: CopilotCommand[] = [
  { label: "/explain BTC", command: "/explain BTC", description: "Get multi-timeframe neural explanation of current BTC trend" },
  { label: "/risk-check", command: "/risk-check", description: "Evaluate overall portfolio VaR and concentration score" },
  { label: "/market-pulse", command: "/market-pulse", description: "Get a quick summary of global sentiment and trends" },
];

export function CopilotWidget() {
  const navigate = useNavigate();
  const [inputValue, setInputValue] = useState("");
  const [chatLog, setChatLog] = useState<{ role: "user" | "copilot"; text: string }[]>([
    { role: "copilot", text: "Ready. Enter an asset or select an institutional command." },
  ]);
  const [isLoading, setIsLoading] = useState(false);

  const handleCommandClick = (cmd: string) => {
    setInputValue(cmd);
  };

  const handleSend = async () => {
    if (!inputValue.trim()) return;
    const userText = inputValue;
    setChatLog((prev) => [...prev, { role: "user", text: userText }]);
    setInputValue("");
    setIsLoading(true);

    // Simulated streaming response of the copilot
    setTimeout(() => {
      let responseText = "Analyzing market structures and trading models...";
      if (userText.toLowerCase().includes("btc")) {
        responseText = "BTC/USDT Model: Trend bullish, volume accelerating. Strong resistance at $98,500. Support at $94,800. Confidence: 89%.";
      } else if (userText.toLowerCase().includes("risk")) {
        responseText = "Portfolio Risk Assessment: Total exposure: $54,200. Value-at-Risk (95%): $1,420. System health check: Normal.";
      } else if (userText.toLowerCase().includes("pulse")) {
        responseText = "Market Pulse: 4H Momentum is positive. High whale volume transfers observed over past 2 hours. Order book skewed to buy-side.";
      }
      setChatLog((prev) => [...prev, { role: "copilot", text: responseText }]);
      setIsLoading(false);
    }, 600);
  };

  return (
    <Card
      className="h-full border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all flex flex-col justify-between"
      role="region"
      aria-label="AI Copilot Command Center"
    >
      <CardContent className="p-2.5 flex flex-col h-full justify-between gap-1.5">
        <div>
          <div className="flex items-center justify-between mb-1.5 pb-1 border-b border-[var(--border-subtle)]">
            <div className="flex items-center gap-1.5 cursor-pointer" onClick={() => navigate("/ai-experience")}>
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">AI Copilot</span>
              <span className="text-[8px] bg-[var(--accent-purple)]/15 text-[var(--accent-purple)] px-1 rounded uppercase tracking-[0.05em] font-mono font-semibold">ACTIVE</span>
            </div>
            <span className="text-[9px] text-[var(--text-muted)] font-mono cursor-pointer" onClick={() => navigate("/ai-experience")}>◈ Link</span>
          </div>

          {/* Quick fast commands */}
          <div className="flex gap-1 mb-2 overflow-x-auto pb-0.5 whitespace-nowrap scrollbar-none">
            {fastCommands.map((fc) => (
              <button
                key={fc.label}
                onClick={() => handleCommandClick(fc.command)}
                className="px-1.5 py-0.5 rounded bg-[var(--bg-elevated)] border border-[var(--border-subtle)] hover:border-[var(--accent-purple)]/40 hover:bg-[var(--bg-hover)] text-[9px] font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all"
                title={fc.description}
              >
                {fc.label}
              </button>
            ))}
          </div>

          {/* Mini terminal display screen */}
          <div className="bg-black/40 rounded p-1.5 border border-[var(--border-subtle)] text-[10px] font-mono h-[85px] overflow-y-auto mb-1.5 space-y-1">
            {chatLog.map((log, index) => (
              <div key={index} className={log.role === "user" ? "text-[var(--text-primary)]" : "text-[var(--accent-purple)]"}>
                <span className="text-[var(--text-muted)]">{log.role === "user" ? "> " : "copilot: "}</span>
                {log.text}
              </div>
            ))}
            {isLoading && (
              <div className="text-[var(--text-muted)] animate-pulse">
                <span>&gt; thinking...</span>
              </div>
            )}
          </div>
        </div>

        {/* Dense Input control panel */}
        <div className="flex gap-1">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSend();
            }}
            placeholder="Type Copilot command..."
            className="flex-1 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded px-2 py-1 text-[10px] font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-purple)]"
            aria-label="Copilot Prompt Input"
          />
          <button
            onClick={handleSend}
            disabled={isLoading}
            className="px-2.5 py-1 rounded bg-[var(--accent-purple)] hover:bg-[var(--accent-purple)]/80 text-[var(--text-inverse)] font-semibold text-[10px] transition-colors"
          >
            EXEC
          </button>
        </div>
      </CardContent>
    </Card>
  );
}

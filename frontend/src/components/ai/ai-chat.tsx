import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

const suggestions = [
  "Analyze BTC/USDT current market regime",
  "What's the risk level of my portfolio?",
  "Show me top trading opportunities",
  "Explain this market regime shift",
];

export function AIChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Welcome, Commander. OLLO Autonomous Intelligence operator terminal is online and synchronized.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = (text: string) => {
    if (!text.trim()) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    setTimeout(() => {
      const responses: Record<string, string> = {
        analyze: "Based on current market data, BTC/USDT is showing bullish momentum with RSI at 58. Volume is above average, suggesting strong participation. Key resistance at $43,500, support at $41,800.",
        risk: "Your portfolio risk profile is LOW. VaR (95%) at 1.2%. Correlation score: 0.32. Leverage: 0.8x. All metrics are within healthy ranges.",
        opportunities: "Top opportunities: 1) BTC/USDT long if it breaks $43,200 resistance. 2) ETH/USDT accumulation at support zone $2,200-$2,250. 3) SOL/USDT short if it fails to hold $140.",
        explain: "Market regime detection analyzes volatility clustering, trend strength, and correlation structures. Current regime: TREND with BULLISH bias — characterized by sustained directional movement and above-average volume.",
      };

      const reply =
        Object.entries(responses).find(([key]) =>
          text.toLowerCase().includes(key),
        )?.[1] ||
        "I'll analyze that for you. Based on the current market context, I recommend monitoring key support/resistance levels before making a decision.";

      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: reply,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setIsTyping(false);
    }, 1200);
  };

  const hasOnlyWelcome = messages.length === 1 && messages[0].id === "welcome";

  return (
    <Card className="h-full flex flex-col min-h-[480px]">
      <CardHeader className="border-b border-[var(--border-subtle)]">
        <div className="flex items-center justify-between">
          <CardTitle>AI Operator Console</CardTitle>
          <span className="text-[10px] font-mono text-[var(--accent-green)] animate-pulse flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-green)]" />
            OLLO CORE ACTIVE
          </span>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col min-h-0 p-0">
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
          {hasOnlyWelcome ? (
            <div className="flex flex-col items-center justify-center h-full py-8 text-center space-y-6">
              {/* Orb breathing container */}
              <div className="relative flex items-center justify-center">
                <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-[var(--accent-blue)]/10 via-[var(--accent-blue)]/5 to-transparent border border-[var(--accent-blue)]/20 animate-pulse flex items-center justify-center">
                  <span className="text-[10px] text-[var(--accent-blue)] font-bold font-mono">OLLO</span>
                </div>
                <div className="absolute inset-0 border border-dashed border-[var(--border-subtle)] rounded-full animate-spin [animation-duration:15s]" />
              </div>

              <div className="space-y-2 max-w-sm">
                <h3 className="text-xs font-bold uppercase tracking-[0.15em] text-[var(--text-primary)]">
                  Welcome, Commander
                </h3>
                <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
                  I'm your OLLO premium operator assistant. I possess full access to real-time orderbooks, whale telemetry, and multi-agent AI council consensus models.
                </p>
                <div className="text-[9px] font-mono text-[var(--accent-blue)] mt-2 uppercase tracking-widest bg-[var(--bg-elevated)] px-2 py-1 rounded inline-block border border-[var(--border-subtle)]">
                  💡 Hint: Choose a query below or command freely
                </div>
              </div>

              <div className="w-full max-w-md pt-2">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left">
                  {suggestions.map((s) => (
                    <button
                      key={s}
                      onClick={() => handleSend(s)}
                      className="p-2.5 rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[11px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--accent-blue)]/40 transition-all text-left font-sans hover:bg-[var(--bg-hover)] flex flex-col justify-between"
                    >
                      <span>{s}</span>
                      <span className="text-[8px] font-mono text-[var(--text-muted)] mt-1.5 self-end">Ask OLLO →</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <AnimatePresence>
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div className={`flex flex-col gap-1 max-w-[85%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
                    <div
                      className={`rounded-xl px-3.5 py-2.5 ${
                        msg.role === "user"
                          ? "bg-[var(--accent-blue)]/15 border border-[var(--accent-blue)]/20 text-[var(--text-primary)]"
                          : "bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--text-secondary)]"
                      }`}
                    >
                      <p className="text-[11px] leading-relaxed whitespace-pre-wrap">
                        {msg.content}
                      </p>
                    </div>
                    <span className="text-[8px] font-mono text-[var(--text-muted)] uppercase tracking-wider px-1">
                      {msg.role === "user" ? "Commander" : "OLLO Operator"} · {msg.timestamp.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false })}
                    </span>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          )}

          {isTyping && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="max-w-[85%] rounded-xl px-3 py-2 bg-[var(--bg-elevated)] border border-[var(--border-subtle)]">
                <div className="flex gap-1.5 items-center">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-blue)] animate-bounce" />
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-blue)] animate-bounce [animation-delay:0.1s]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-blue)] animate-bounce [animation-delay:0.2s]" />
                  <span className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-widest ml-1.5">OLLO is thinking...</span>
                </div>
              </div>
            </motion.div>
          )}
          <div ref={endRef} />
        </div>

        {!hasOnlyWelcome && (
          <div className="px-4 pb-3 border-t border-[var(--border-subtle)] pt-3">
            <div className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider mb-2">
              Suggested Directives
            </div>
            <div className="flex flex-wrap gap-1.5">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => handleSend(s)}
                  className="px-2 py-1 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[10px] text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:border-[var(--border-default)] transition-all"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="border-t border-[var(--border-subtle)] p-3 bg-[var(--bg-surface)]/40">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend(input);
              }}
              placeholder="Command OLLO Assistant..."
              className="flex-1 bg-[var(--bg-base)] rounded-lg px-3 py-2 text-xs font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] border border-[var(--border-default)] focus:outline-none focus:border-[var(--accent-blue)] focus:ring-1 focus:ring-[var(--accent-blue)]"
            />
            <Button
              onClick={() => handleSend(input)}
              disabled={!input.trim()}
              variant="primary"
              size="sm"
              className="h-8 font-mono"
            >
              Send
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

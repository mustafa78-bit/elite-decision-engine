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
      content: "I'm your AI trading assistant. Ask me anything about markets, analysis, or your portfolio.",
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

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle>AI Assistant</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col min-h-0 p-0">
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
          <AnimatePresence>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-xl px-3 py-2 ${
                    msg.role === "user"
                      ? "bg-[var(--accent-blue)]/15 border border-[var(--accent-blue)]/20 text-[var(--text-primary)]"
                      : "bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--text-secondary)]"
                  }`}
                >
                  <p className="text-[11px] leading-relaxed whitespace-pre-wrap">
                    {msg.content}
                  </p>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          {isTyping && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="max-w-[85%] rounded-xl px-3 py-2 bg-[var(--bg-elevated)] border border-[var(--border-subtle)]">
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-muted)] animate-bounce" />
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-muted)] animate-bounce [animation-delay:0.1s]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-muted)] animate-bounce [animation-delay:0.2s]" />
                </div>
              </div>
            </motion.div>
          )}
          <div ref={endRef} />
        </div>

        {messages.length === 1 && (
          <div className="px-4 pb-3">
            <div className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider mb-2">
              Suggestions
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

        <div className="border-t border-[var(--border-subtle)] p-3">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend(input);
              }}
              placeholder="Ask anything..."
              className="flex-1 bg-[var(--bg-base)] rounded-lg px-3 py-2 text-xs font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] border border-[var(--border-default)] focus:outline-none focus:border-[var(--accent-blue)]"
            />
            <button
              onClick={() => handleSend(input)}
              disabled={!input.trim()}
              className="px-3 py-2 rounded-lg bg-[var(--accent-blue)] text-white text-xs font-mono hover:bg-[var(--accent-blue)]/90 disabled:opacity-40 transition-all"
            >
              Send
            </button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

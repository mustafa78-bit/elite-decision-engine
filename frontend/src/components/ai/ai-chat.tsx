import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { apiFetch } from "../../api/client";

interface LinkItem {
  label: string;
  path: string;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  suggestions?: string[];
  links?: LinkItem[];
  metrics?: Record<string, any>;
}

const DEFAULT_SUGGESTIONS = [
  "Why should I buy BTC?",
  "What changed in the last hour?",
  "What are the biggest portfolio risks?",
  "What happens if BTC drops 10%?",
  "Show me the best opportunities today.",
];

// Helper to format simple markdown-like elements (bold, code, headers, bullets, and tables) safely in JSX
function formatReplyText(text: string) {
  const lines = text.split("\n");
  return lines.map((line, index) => {
    let cleanLine = line.trim();

    // Check for Headers
    if (cleanLine.startsWith("###")) {
      return (
        <h3 key={index} className="text-xs font-semibold text-[var(--text-primary)] mt-3 mb-1.5 border-b border-[var(--border-subtle)] pb-1">
          {cleanLine.replace("###", "").trim()}
        </h3>
      );
    }
    if (cleanLine.startsWith("####")) {
      return (
        <h4 key={index} className="text-[11px] font-semibold text-[var(--text-primary)] mt-2 mb-1">
          {cleanLine.replace("####", "").trim()}
        </h4>
      );
    }

    // Check for bullet lists
    if (cleanLine.startsWith("-") || cleanLine.startsWith("*")) {
      const content = cleanLine.substring(1).trim();
      return (
        <li key={index} className="ml-3 list-disc text-[10px] leading-relaxed text-[var(--text-secondary)]">
          {parseInlineFormatting(content)}
        </li>
      );
    }

    // Check for numbered lists
    const numMatch = cleanLine.match(/^(\d+)\.\s(.*)/);
    if (numMatch) {
      return (
        <li key={index} className="ml-3 list-decimal text-[10px] leading-relaxed text-[var(--text-secondary)]">
          {parseInlineFormatting(numMatch[2])}
        </li>
      );
    }

    // Check for tables
    if (cleanLine.startsWith("|")) {
      if (cleanLine.includes("---")) return null; // skip separator row
      const cells = cleanLine.split("|").map(c => c.trim()).filter(Boolean);
      return (
        <div key={index} className="flex gap-2 text-[9px] font-mono py-1 border-b border-[var(--border-subtle)]/50">
          {cells.map((cell, cIdx) => (
            <span key={cIdx} className="flex-1 min-w-[60px] text-[var(--text-secondary)]">
              {parseInlineFormatting(cell)}
            </span>
          ))}
        </div>
      );
    }

    if (!cleanLine) {
      return <div key={index} className="h-1.5" />;
    }

    return (
      <p key={index} className="text-[10px] leading-relaxed text-[var(--text-secondary)] mb-1">
        {parseInlineFormatting(cleanLine)}
      </p>
    );
  });
}

function parseInlineFormatting(text: string) {
  // Simple regex to parse **bold** and `code` inline elements
  const parts = [];
  let currentStr = text;
  let keyIdx = 0;

  while (currentStr.length > 0) {
    const boldMatch = currentStr.match(/\*\*(.*?)\*\*/);
    const codeMatch = currentStr.match(/`(.*?)`/);

    const boldIdx = boldMatch && boldMatch.index !== undefined ? boldMatch.index : Infinity;
    const codeIdx = codeMatch && codeMatch.index !== undefined ? codeMatch.index : Infinity;

    if (boldIdx === Infinity && codeIdx === Infinity) {
      parts.push(<span key={keyIdx++}>{currentStr}</span>);
      break;
    }

    if (boldIdx < codeIdx) {
      if (boldIdx > 0) {
        parts.push(<span key={keyIdx++}>{currentStr.substring(0, boldIdx)}</span>);
      }
      const val = boldMatch ? boldMatch[1] : "";
      parts.push(<strong key={keyIdx++} className="font-bold text-[var(--text-primary)]">{val}</strong>);
      currentStr = currentStr.substring(boldIdx + (boldMatch ? boldMatch[0].length : 0));
    } else {
      if (codeIdx > 0) {
        parts.push(<span key={keyIdx++}>{currentStr.substring(0, codeIdx)}</span>);
      }
      const val = codeMatch ? codeMatch[1] : "";
      parts.push(
        <code key={keyIdx++} className="px-1 py-0.5 rounded bg-[var(--bg-base)] text-[var(--accent-cyan)] font-mono text-[9px] border border-[var(--border-subtle)]">
          {val}
        </code>
      );
      currentStr = currentStr.substring(codeIdx + (codeMatch ? codeMatch[0].length : 0));
    }
  }

  return parts;
}

export function AIChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "### Welcome to Elite Decision Assistant!\nI am your conversational intelligence copilot. I am fully integrated with the Decision Engine, Portfolio Stats, Risk Controls, and Market Indicators.\n\nAsk me anything or choose one of the contextual suggestions below.",
      timestamp: new Date(),
      suggestions: DEFAULT_SUGGESTIONS,
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (endRef.current && typeof endRef.current.scrollIntoView === "function") {
      endRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isTyping]);

  const handleSend = async (text: string) => {
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

    try {
      // Call the new backend copilot API
      const activeSymbol = localStorage.getItem("active_symbol") || "BTC";
      const data = await apiFetch<{
        reply: string;
        suggestions: string[];
        links: LinkItem[];
        metrics: Record<string, any>;
      }>("/copilot/chat", {
        method: "POST",
        body: JSON.stringify({ message: text, symbol: activeSymbol }),
      });

      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.reply,
        timestamp: new Date(),
        suggestions: data.suggestions || DEFAULT_SUGGESTIONS,
        links: data.links || [],
        metrics: data.metrics || {},
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error("Failed to query Copilot API", err);
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "### ⚠️ API Connection Error\nI was unable to connect to the Decision Engine's Copilot service. Please check if the backend service is running and properly configured.",
        timestamp: new Date(),
        suggestions: DEFAULT_SUGGESTIONS,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const lastMessage = messages[messages.length - 1];
  const activeSuggestions = lastMessage?.role === "assistant" ? lastMessage.suggestions : DEFAULT_SUGGESTIONS;

  return (
    <Card className="h-full flex flex-col bg-[var(--bg-surface)] border border-[var(--border-subtle)] shadow-lg rounded-xl overflow-hidden">
      <CardHeader className="border-b border-[var(--border-subtle)] bg-[var(--bg-base)]/50 py-3 px-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[var(--accent-purple)] animate-pulse shadow-[0_0_8px_var(--accent-purple)]" />
            <CardTitle className="text-xs font-semibold text-[var(--text-primary)] font-mono">
              Elite AI Copilot
            </CardTitle>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[9px] font-mono text-[var(--text-muted)] bg-[var(--bg-elevated)] px-2 py-0.5 rounded border border-[var(--border-subtle)]">
              Explainable Mode Active
            </span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col min-h-0 p-0">
        {/* Messages List */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 font-sans">
          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[88%] rounded-xl px-4 py-3 shadow-md ${
                    msg.role === "user"
                      ? "bg-[var(--accent-blue)]/10 border border-[var(--accent-blue)]/20 text-[var(--text-primary)]"
                      : "bg-[var(--bg-elevated)] border border-[var(--border-subtle)]"
                  }`}
                >
                  <div className="space-y-1.5">
                    {msg.role === "user" ? (
                      <p className="text-[10px] leading-relaxed text-[var(--text-primary)]">
                        {msg.content}
                      </p>
                    ) : (
                      formatReplyText(msg.content)
                    )}
                  </div>

                  {/* Links / Actions */}
                  {msg.links && msg.links.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3 pt-2.5 border-t border-[var(--border-subtle)]/50">
                      {msg.links.map((link, idx) => (
                        <Link
                          key={idx}
                          to={link.path}
                          className="px-2.5 py-1 rounded bg-[var(--accent-blue)]/20 hover:bg-[var(--accent-blue)]/30 border border-[var(--accent-blue)]/30 text-[9px] font-semibold font-mono text-[var(--text-primary)] transition-all flex items-center gap-1"
                        >
                          <span>➔</span>
                          <span>{link.label}</span>
                        </Link>
                      ))}
                    </div>
                  )}

                  {/* Technical Metrics Breakdown */}
                  {msg.metrics && Object.keys(msg.metrics).length > 0 && msg.metrics.status !== "fallback" && (
                    <div className="mt-2.5 p-2 bg-[var(--bg-base)]/50 rounded border border-[var(--border-subtle)] text-[8px] font-mono text-[var(--text-muted)] space-y-0.5">
                      <div className="text-[9px] font-bold text-[var(--text-secondary)] mb-1">
                        🔬 Underneath Explainable AI Data
                      </div>
                      {Object.entries(msg.metrics).map(([k, v]) => (
                        <div key={k} className="flex justify-between">
                          <span>{k}:</span>
                          <span className="text-[var(--text-secondary)]">{JSON.stringify(v)}</span>
                        </div>
                      ))}
                    </div>
                  )}
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
              <div className="max-w-[85%] rounded-xl px-4 py-3 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] shadow-sm">
                <div className="flex items-center gap-2">
                  <span className="text-[9px] font-mono text-[var(--text-muted)]">Analyzing platform metrics</span>
                  <div className="flex gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-purple)] animate-bounce" />
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-purple)] animate-bounce [animation-delay:0.1s]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-purple)] animate-bounce [animation-delay:0.2s]" />
                  </div>
                </div>
              </div>
            </motion.div>
          )}
          <div ref={endRef} />
        </div>

        {/* Dynamic Contextual suggestions */}
        {activeSuggestions && activeSuggestions.length > 0 && (
          <div className="px-4 pb-3 pt-2 bg-[var(--bg-base)]/30 border-t border-[var(--border-subtle)]/30">
            <div className="text-[8px] text-[var(--text-muted)] font-mono uppercase tracking-wider mb-2">
              Contextual Suggestions
            </div>
            <div className="flex flex-wrap gap-1.5">
              {activeSuggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => handleSend(s)}
                  className="px-2.5 py-1 rounded-lg bg-[var(--bg-elevated)] hover:bg-[var(--bg-hover)] border border-[var(--border-subtle)] text-[9px] font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-default)] transition-all cursor-pointer"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input area */}
        <div className="border-t border-[var(--border-subtle)] p-3 bg-[var(--bg-base)]/60">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend(input);
              }}
              placeholder="Ask me: 'Why should I buy BTC?' or 'What are the biggest risks?'..."
              className="flex-1 bg-[var(--bg-base)] rounded-lg px-3 py-2 text-xs font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] border border-[var(--border-default)] focus:outline-none focus:border-[var(--accent-purple)] transition-all"
            />
            <button
              onClick={() => handleSend(input)}
              disabled={!input.trim() || isTyping}
              className="px-4 py-2 rounded-lg bg-[var(--accent-purple)] text-white text-xs font-semibold font-mono hover:bg-[var(--accent-purple)]/90 disabled:opacity-40 transition-all cursor-pointer"
            >
              Send
            </button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

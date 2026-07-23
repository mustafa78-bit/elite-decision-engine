import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  X,
  Maximize2,
  Minimize2,
  Send,
  Terminal,
  Activity
} from "lucide-react";
import { DecisionExplanationCard } from "./decision-explanation-card";
import type { RichOLLOMessage } from "../../types/ollo";
import { useNavigate } from "react-router-dom";

export function OLLOPanel() {
  const [panelState, setPanelState] = useState<"collapsed" | "expanded" | "conversation">("collapsed");
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const navigate = useNavigate();

  // Seeded premium AI operator messages
  const [messages, setMessages] = useState<RichOLLOMessage[]>([
    {
      id: "init",
      sender: "ollo",
      timestamp: new Date().toISOString(),
      title: "OLLO OPERATOR ONLINE",
      summary: "I am actively monitoring the perpetual futures markets and on-chain whale inflows. All core modules are at full operational readiness.",
      reasoning: ["System latency checks 14ms", "Hyperliquid ticker connections active", "Evidence engines sync complete"],
      text: "Operator initialized. Select an action or query me directly."
    },
    {
      id: "decision-buy",
      sender: "ollo",
      timestamp: new Date().toISOString(),
      title: "BUY SIGNAL: BTC/USDT Perpetual",
      summary: "Extremely strong alignment detected across high timeframe momentum, whale wallet flows, and positive funding rate structures.",
      confidence: 92,
      reasoning: [
        "Whale accumulation: Large wallets accumulated > 4,500 BTC in 24 hours.",
        "HTF trend bullish: 4h and 1d EMA structure fully aligned upward.",
        "Funding positive: Longs paying shorts moderately, indicating healthy spot-driven premium.",
        "News positive: Institutional ETF flows hit a consecutive 5-day record high."
      ],
      evidence: [
        { type: "whale", description: "Inflow delta +4.5k BTC", confidence: 95 },
        { type: "technical", description: "4h EMA 20/50 Golden Cross", confidence: 91 },
        { type: "funding", description: "Perp rate at +0.012% per 8h", confidence: 88 },
        { type: "news", description: "ETF net inflows +$450M", confidence: 90 }
      ],
      risk: "LOW",
      actions: [
        { id: "exec-btc", label: "Execute LONG BTC", type: "execute_trade", payload: { symbol: "BTC", side: "LONG" } },
        { id: "nav-portfolio", label: "Open Portfolio", type: "navigate", payload: { path: "/portfolio-detail" } }
      ]
    },
    {
      id: "decision-wait",
      sender: "ollo",
      timestamp: new Date().toISOString(),
      title: "WAIT SIGNAL: ETH/USDT Perpetual",
      summary: "Price consolidated below strong key resistance. Order book bid depth is thin, indicating potential liquidity sweeps.",
      confidence: 68,
      reasoning: [
        "Potential resistance: Approaching key 1d supply zone at $3,550.",
        "Weak BTC dominance: Capital rotating out of alts into BTC shelter.",
        "Order book imbalance: Sell side asks outweighing bids by 2.2x."
      ],
      evidence: [
        { type: "technical", description: "RSI overbought on 4h (74)", confidence: 85 },
        { type: "portfolio", description: "Existing exposure in ETH is high", confidence: 90 }
      ],
      risk: "MODERATE",
      actions: [
        { id: "nav-scanner", label: "Monitor Scanner", type: "navigate", payload: { path: "/scanner" } }
      ]
    }
  ]);

  const handleAction = (_actionId: string, actionType: string, payload?: any) => {
    if (actionType === "navigate" && payload?.path) {
      navigate(payload.path);
      setPanelState("collapsed");
    } else if (actionType === "execute_trade") {
      // Simulate trade execution
      const alertMsg: RichOLLOMessage = {
        id: `alert-${Date.now()}`,
        sender: "ollo",
        timestamp: new Date().toISOString(),
        title: "TRADE SENT",
        summary: `Paper trade order generated successfully for ${payload?.symbol} ${payload?.side}. Sent to Execution Engine.`,
        reasoning: ["Slippage: minimal", "Sizing: ATR-based position size evaluated"],
        risk: "LOW"
      };
      setMessages(prev => [...prev, alertMsg]);
    }
  };

  const handleSend = () => {
    if (!input.trim()) return;

    const userMsg: RichOLLOMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      timestamp: new Date().toISOString(),
      text: input
    };

    setMessages(prev => [...prev, userMsg]);
    const currentQuery = input.toLowerCase();
    setInput("");
    setIsTyping(true);

    setTimeout(() => {
      let reply: RichOLLOMessage;

      if (currentQuery.includes("btc") || currentQuery.includes("bitcoin")) {
        reply = {
          id: `ollo-${Date.now()}`,
          sender: "ollo",
          timestamp: new Date().toISOString(),
          title: "BTC MARKET BRIEFING",
          summary: "Bitcoin continues to consolidate in a strong bullish regime. Key volume structures support continuation.",
          confidence: 89,
          reasoning: [
            "Whale accumulation: Net positive wallet flows over 3 days.",
            "HTF trend remains bullish with solid daily support at $64k.",
            "Funding rates are completely normal and spot premium is positive."
          ],
          evidence: [
            { type: "technical", description: "Daily EMA 20 trending up", confidence: 92 },
            { type: "whale", description: "Coinbase premium delta positive", confidence: 85 }
          ],
          risk: "LOW",
          actions: [
            { id: "exec-btc-long", label: "Execute BTC LONG", type: "execute_trade", payload: { symbol: "BTC", side: "LONG" } }
          ]
        };
      } else if (currentQuery.includes("portfolio") || currentQuery.includes("risk")) {
        reply = {
          id: `ollo-${Date.now()}`,
          sender: "ollo",
          timestamp: new Date().toISOString(),
          title: "PORTFOLIO & RISK BRIEFING",
          summary: "Your portfolio has optimized exposure. Leveraged drawdown index is strictly nominal.",
          confidence: 96,
          reasoning: [
            "Total exposure: 35.5% of total collateralized capital.",
            "Drawdown index: minimal (under 0.8% peak to trough).",
            "Consensus: AI Council recommends adding small breakout weights."
          ],
          evidence: [
            { type: "portfolio", description: "Equity correlation score 0.32", confidence: 95 }
          ],
          risk: "LOW",
          actions: [
            { id: "nav-port-detail", label: "Open Portfolio", type: "navigate", payload: { path: "/portfolio-detail" } }
          ]
        };
      } else if (currentQuery.includes("whale")) {
        reply = {
          id: `ollo-${Date.now()}`,
          sender: "ollo",
          timestamp: new Date().toISOString(),
          title: "WHALE ACTIVITY ANALYSIS",
          summary: "On-chain indicators show major wallet shifts into high-cap coins.",
          confidence: 90,
          reasoning: [
            "Whale accumulation: Accumulation score increased to 92/100.",
            "Exchange flow: Outflows from centralized exchanges remain elevated."
          ],
          evidence: [
            { type: "whale", description: "Transaction volume > 10M USD", confidence: 91 }
          ],
          risk: "LOW"
        };
      } else {
        reply = {
          id: `ollo-${Date.now()}`,
          sender: "ollo",
          timestamp: new Date().toISOString(),
          title: "OPERATOR RECOMMENDATION",
          summary: "Analyzing market shifts. Current market volatility requires patience.",
          text: "Understood, Commander. All systems are being scanned for optimal entry points based on your query.",
          confidence: 75,
          reasoning: [
            "Awaiting consensus confirmation",
            "Reading global liquidity profiles",
            "Evaluating risk indices"
          ],
          risk: "MODERATE"
        };
      }

      setMessages(prev => [...prev, reply]);
      setIsTyping(false);
    }, 1500);
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      <AnimatePresence>
        {/* COLLAPSED STATE: Floating Operator Orb */}
        {panelState === "collapsed" && (
          <motion.button
            key="collapsed-orb"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            onClick={() => setPanelState("expanded")}
            className="group relative flex items-center justify-center w-14 h-14 rounded-full bg-[#101A2E] border border-[var(--border-subtle)] cursor-pointer overflow-hidden shadow-[0_0_20px_rgba(59,130,246,0.3)] hover:shadow-[0_0_30px_rgba(59,130,246,0.5)] transition-all"
            style={{
              animation: "ollo-breathe 4s ease-in-out infinite, ollo-glow 4s ease-in-out infinite"
            }}
          >
            {/* Volumetric glow effects */}
            <div className="absolute inset-0 bg-radial-gradient from-blue-500/20 via-transparent to-transparent pointer-events-none" />
            <Bot className="w-6 h-6 text-blue-400 group-hover:scale-110 transition-transform" />

            {/* Mini ping status */}
            <span className="absolute top-3 right-3 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
          </motion.button>
        )}

        {/* EXPANDED STATE: Sidebar Style AI Workspace */}
        {panelState === "expanded" && (
          <motion.div
            key="expanded-panel"
            initial={{ opacity: 0, x: 100, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 100, scale: 0.95 }}
            className="w-[420px] h-[650px] bg-[#0B1220] border border-[var(--border-subtle)] rounded-2xl shadow-2xl flex flex-col overflow-hidden"
          >
            {/* Header bar */}
            <div className="flex items-center justify-between px-4 py-3.5 bg-[#101A2E] border-b border-[var(--border-subtle)]">
              <div className="flex items-center gap-2">
                <Bot className="w-5 h-5 text-blue-400" />
                <div>
                  <span className="text-xs font-mono font-bold text-[var(--text-primary)]">OLLO OPERATOR</span>
                  <div className="flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
                    <span className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider">active</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPanelState("conversation")}
                  className="p-1.5 rounded-md hover:bg-[#162338] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                  title="Full Workspace Screen"
                >
                  <Maximize2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setPanelState("collapsed")}
                  className="p-1.5 rounded-md hover:bg-[#162338] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Quick stats / telemetry bar */}
            <div className="flex items-center justify-between px-4 py-2 bg-[#162338]/40 border-b border-[var(--border-subtle)] text-[10px] font-mono text-[var(--text-muted)]">
              <span className="flex items-center gap-1">
                <Activity className="w-3 h-3 text-blue-400" />
                SYS STATUS: NOMINAL
              </span>
              <span>PING: 14ms</span>
            </div>

            {/* Content Feed */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg) => (
                <div key={msg.id}>
                  {msg.sender === "user" ? (
                    <div className="flex justify-end">
                      <div className="max-w-[85%] rounded-xl px-3 py-2 bg-[var(--accent-blue)]/10 border border-[var(--accent-blue)]/20 text-xs font-mono text-[var(--text-primary)]">
                        {msg.text}
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {msg.title ? (
                        <DecisionExplanationCard message={msg} onAction={handleAction} />
                      ) : (
                        <div className="flex justify-start">
                          <div className="max-w-[85%] rounded-xl px-3 py-2 bg-[#101A2E] border border-[var(--border-subtle)] text-xs font-mono text-[var(--text-secondary)]">
                            {msg.text}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}

              {isTyping && (
                <div className="flex justify-start">
                  <div className="rounded-xl px-3 py-2 bg-[#101A2E] border border-[var(--border-subtle)] text-xs font-mono text-[var(--text-muted)]">
                    <div className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-muted)] animate-bounce" />
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-muted)] animate-bounce [animation-delay:0.15s]" />
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-muted)] animate-bounce [animation-delay:0.3s]" />
                      <span className="ml-1 text-[10px] uppercase">OLLO is analyzing...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Prompt bar */}
            <div className="p-3 border-t border-[var(--border-subtle)] bg-[#101A2E]/80">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleSend();
                  }}
                  placeholder="Explain BTC, Why WAIT, Show Whale Activity..."
                  className="flex-1 bg-[#0B1220] rounded-lg px-3 py-2 text-xs font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] border border-[var(--border-subtle)] focus:outline-none focus:border-blue-500"
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim()}
                  className="p-2.5 rounded-lg bg-[var(--accent-blue)] text-white hover:bg-[var(--accent-blue)]/90 disabled:opacity-40 transition-all cursor-pointer"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {/* FULL CONVERSATION STATE: Large Center Workspace Overlay */}
        {panelState === "conversation" && (
          <motion.div
            key="conversation-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-[#060A13]/85 backdrop-blur-md flex items-center justify-center z-50 p-6"
            onClick={(e) => {
              if (e.target === e.currentTarget) setPanelState("expanded");
            }}
          >
            <motion.div
              initial={{ scale: 0.95, y: 15 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 15 }}
              className="w-full max-w-5xl h-[85vh] bg-[#0B1220] border border-[var(--border-subtle)] rounded-2xl overflow-hidden shadow-2xl flex flex-col"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 bg-[#101A2E] border-b border-[var(--border-subtle)]">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/20">
                    <Bot className="w-6 h-6 text-blue-400" />
                  </div>
                  <div>
                    <h2 className="text-sm font-bold font-mono text-[var(--text-primary)] tracking-wide">
                      OLLO AI INTEL OPERATOR WORKSPACE
                    </h2>
                    <p className="text-[10px] font-mono text-emerald-400 uppercase tracking-widest">
                      high-fidelity analytical suite online
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPanelState("expanded")}
                    className="p-2 rounded-lg hover:bg-[#162338] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                  >
                    <Minimize2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setPanelState("collapsed")}
                    className="p-2 rounded-lg hover:bg-[#162338] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Main Workspace Layout (2 columns: telemetry & messages) */}
              <div className="flex-1 flex overflow-hidden">

                {/* Left side: Telemetry & Status information */}
                <div className="w-[320px] border-r border-[var(--border-subtle)] bg-[#101A2E]/40 p-4 space-y-4 overflow-y-auto">
                  <div className="rounded-xl border border-[#263956]/40 bg-[#101A2E] p-3">
                    <div className="flex items-center gap-2 text-xs font-mono font-bold text-[var(--text-primary)] uppercase tracking-wider mb-2">
                      <Terminal className="w-4 h-4 text-blue-400" />
                      Operator Status
                    </div>
                    <div className="space-y-1.5 font-mono text-[11px] text-[var(--text-secondary)]">
                      <div className="flex justify-between">
                        <span>Provider:</span>
                        <span className="text-[var(--text-primary)] font-semibold">NVIDIA</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Model:</span>
                        <span className="text-[var(--text-primary)]">meta/llama-3-70b</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Telemetry sync:</span>
                        <span className="text-emerald-400">NOMINAL</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Subsystem latency:</span>
                        <span className="text-blue-400">14.2ms</span>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-xl border border-[#263956]/40 bg-[#101A2E] p-3">
                    <div className="flex items-center gap-2 text-xs font-mono font-bold text-[var(--text-primary)] uppercase tracking-wider mb-2">
                      <Activity className="w-4 h-4 text-emerald-400" />
                      Live Diagnostics
                    </div>
                    <div className="space-y-2">
                      <div>
                        <div className="flex justify-between text-[9px] font-mono text-[var(--text-muted)] mb-1">
                          <span>COUNCIL CONSENSUS LEVEL</span>
                          <span>92%</span>
                        </div>
                        <div className="h-1.5 w-full bg-[#162338] rounded-full overflow-hidden">
                          <div className="h-full bg-emerald-500" style={{ width: "92%" }} />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-[9px] font-mono text-[var(--text-muted)] mb-1">
                          <span>WHALE ACCUMULATION INDEX</span>
                          <span>85%</span>
                        </div>
                        <div className="h-1.5 w-full bg-[#162338] rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500" style={{ width: "85%" }} />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-xl border border-[#263956]/40 bg-[#101A2E] p-3 space-y-2">
                    <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase tracking-wider block">
                      Quick Intel Queries
                    </span>
                    <button
                      onClick={() => { setInput("Explain BTC"); }}
                      className="w-full text-left px-2.5 py-1.5 rounded bg-[#162338]/60 hover:bg-[#162338] text-[11px] font-mono text-[var(--text-secondary)] border border-[#263956]/20 transition-all"
                    >
                      &gt; Explain BTC
                    </button>
                    <button
                      onClick={() => { setInput("Why WAIT?"); }}
                      className="w-full text-left px-2.5 py-1.5 rounded bg-[#162338]/60 hover:bg-[#162338] text-[11px] font-mono text-[var(--text-secondary)] border border-[#263956]/20 transition-all"
                    >
                      &gt; Why WAIT?
                    </button>
                    <button
                      onClick={() => { setInput("Show Whale Activity"); }}
                      className="w-full text-left px-2.5 py-1.5 rounded bg-[#162338]/60 hover:bg-[#162338] text-[11px] font-mono text-[var(--text-secondary)] border border-[#263956]/20 transition-all"
                    >
                      &gt; Show Whale Activity
                    </button>
                  </div>
                </div>

                {/* Right side: Chat Feed & Cards */}
                <div className="flex-1 flex flex-col overflow-hidden bg-[#0B1220]">
                  <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {messages.map((msg) => (
                      <div key={msg.id} className="max-w-3xl mx-auto">
                        {msg.sender === "user" ? (
                          <div className="flex justify-end">
                            <div className="rounded-xl px-4 py-2.5 bg-[var(--accent-blue)]/10 border border-[var(--accent-blue)]/20 text-xs font-mono text-[var(--text-primary)]">
                              {msg.text}
                            </div>
                          </div>
                        ) : (
                          <div className="space-y-3">
                            {msg.title ? (
                              <DecisionExplanationCard message={msg} onAction={handleAction} />
                            ) : (
                              <div className="flex justify-start">
                                <div className="rounded-xl px-4 py-2.5 bg-[#101A2E] border border-[var(--border-subtle)] text-xs font-mono text-[var(--text-secondary)] leading-relaxed">
                                  {msg.text}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}

                    {isTyping && (
                      <div className="max-w-3xl mx-auto flex justify-start">
                        <div className="rounded-xl px-4 py-2.5 bg-[#101A2E] border border-[var(--border-subtle)] text-xs font-mono text-[var(--text-muted)]">
                          <div className="flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-muted)] animate-bounce" />
                            <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-muted)] animate-bounce [animation-delay:0.15s]" />
                            <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-muted)] animate-bounce [animation-delay:0.3s]" />
                            <span className="ml-1 text-[10px] uppercase">Evaluating market structures...</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Input Footer */}
                  <div className="p-4 border-t border-[var(--border-subtle)] bg-[#101A2E]/60">
                    <div className="max-w-3xl mx-auto flex gap-3">
                      <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleSend();
                        }}
                        placeholder="Ask OLLO Operator about market briefs, whale activities, or custom prompts..."
                        className="flex-1 bg-[#0B1220] rounded-xl px-4 py-3 text-xs font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] border border-[var(--border-subtle)] focus:outline-none focus:border-blue-500"
                      />
                      <button
                        onClick={handleSend}
                        disabled={!input.trim()}
                        className="px-5 py-3 rounded-xl bg-[var(--accent-blue)] text-white hover:bg-[var(--accent-blue)]/90 disabled:opacity-40 transition-all font-mono text-xs flex items-center gap-2 cursor-pointer"
                      >
                        <span>Send Query</span>
                        <Send className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>

              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
export default OLLOPanel;

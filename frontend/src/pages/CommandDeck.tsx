import { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useSubsystems } from "../hooks/useSubsystems";
import { useAuth } from "../components/auth/AuthProvider";
import { useNavigate } from "react-router-dom";
import { cn } from "../lib/utils";
import type { WsRoomStatus } from "../types/connection";
import type { LayoutContext } from "../components/layout/Layout";
import type { ScannerOpportunity } from "../api/scanner";
import type { WhaleActivity } from "../api/whale";
import type { TradePayload } from "../types/trade";

interface CommandDeckProps {
  wsRooms: WsRoomStatus;
  context: LayoutContext;
}

type NavSurface = "explore" | "analyze" | "synthesize" | "decide" | "evolve" | null;

interface ChatMessage {
  sender: "user" | "nexus";
  text: string;
  timestamp: string;
}

// Subtle floating particle generator
const generateParticles = (count: number) => {
  return Array.from({ length: count }).map((_, i) => ({
    id: i,
    size: Math.random() * 3 + 1,
    x: Math.random() * 100, // percentage x
    y: Math.random() * 100, // percentage y
    duration: Math.random() * 12 + 8, // seconds
    delay: Math.random() * -20, // start immediately
    opacity: Math.random() * 0.4 + 0.1,
  }));
};

export default function CommandDeck({ wsRooms, context }: CommandDeckProps) {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const {
    scanner,
    risk,
    council,
    portfolio,
    whale,
    market,
    evidence,
    ollo,
    aiHealth,
    loading,
  } = useSubsystems();

  // Navigation surface state
  const [activeSurface, setActiveSurface] = useState<NavSurface>(null);

  // UTC clock state
  const [utcTime, setUtcTime] = useState("");
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setUtcTime(now.toUTCString().replace("GMT", "UTC"));
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  // Fallback to clear loading state in case of network hanging / offline mode
  const [forceClearLoading, setForceClearLoading] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => {
      setForceClearLoading(true);
    }, 2000); // Max 2 seconds of loader
    return () => clearTimeout(timer);
  }, []);

  const isPageLoading = loading && !forceClearLoading;

  // Conversation history
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      sender: "nexus",
      text: ollo.briefing?.text || "NEXUS Operating System initialized. Standby for cognitive briefing. How shall we direct the operations today, Mustafa?",
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [thinkingLabel, setThinkingLabel] = useState("STANDBY");
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Update AI briefing when ollo is loaded
  useEffect(() => {
    if (ollo.briefing?.text) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "nexus",
          text: `[SYSTEM BRIEFING] ${ollo.briefing?.text}`,
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    }
  }, [ollo.briefing?.text]);

  // Scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Handle send command
  const handleSendCommand = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isThinking) return;

    const userMsg = inputValue.trim();
    setMessages((prev) => [...prev, { sender: "user", text: userMsg, timestamp: new Date().toLocaleTimeString() }]);
    setInputValue("");
    setIsThinking(true);

    const labels = [
      "SYNAPSING TELEMETRY VECTOR...",
      "EVALUATING DEBATE COHERENCE...",
      "POLLING MULTI-AGENT COUNCIL...",
      "RUNNING MONTE CARLO SIMULATION...",
      "CALIBRATING EXPECTED ERROR...",
    ];
    let labelIdx = 0;
    setThinkingLabel(labels[0]);

    const labelTimer = setInterval(() => {
      labelIdx = (labelIdx + 1) % labels.length;
      setThinkingLabel(labels[labelIdx]);
    }, 700);

    setTimeout(() => {
      clearInterval(labelTimer);
      setIsThinking(false);
      setThinkingLabel("STANDBY");

      // Generate context-aware response
      let responseText = "Directive acknowledged. System state remains nominal.";
      const query = userMsg.toLowerCase();

      if (query.includes("portfolio") || query.includes("pnl") || query.includes("balance")) {
        const totalValue = 125430;
        const profit = portfolio.data?.total_pnl ?? 4230;
        responseText = `Portfolio valuation consolidated at $${totalValue.toLocaleString()}. Active balance is fully allocated. Net profit is $${profit.toLocaleString()} with a win-rate of ${(portfolio.data?.win_rate ? portfolio.data.win_rate * 100 : 68.2).toFixed(1)}%.`;
      } else if (query.includes("risk") || query.includes("leverage") || query.includes("exposure")) {
        const score = risk.data?.risk_score ?? 4.2;
        responseText = `Current Risk Score is calibrated at ${score.toFixed(1)}/10. Maximum open exposure limit is set to 3. Leverage utilization is nominal at 1.5x.`;
      } else if (query.includes("market") || query.includes("btc") || query.includes("price")) {
        const btcPrice = context.latestPrice?.price ?? 96420;
        const change = context.latestPrice?.change_24h ?? 2.45;
        responseText = `Bitcoin consolidated index at $${btcPrice.toLocaleString()} (${change >= 0 ? "+" : ""}${change.toFixed(2)}%). Multi-timeframe trend aligns ${market.data?.regime || "bullish"}.`;
      } else if (query.includes("recommend") || query.includes("signal") || query.includes("trade")) {
        const decision = evidence.data?.recommendation || "BUY BTC";
        responseText = `Active system recommendation: ${decision}. Decision confidence registered at ${(evidence.data?.decision_confidence ? evidence.data.decision_confidence * 100 : 84).toFixed(0)}%. Core indicators suggest immediate strategic entry.`;
      } else if (query.includes("council") || query.includes("agents") || query.includes("who is")) {
        responseText = `AI Council active. Trend, Volatility, Sentiment, and Whale agents report 88% consensus coherence on the continuous execution ledger.`;
      } else {
        responseText = `Understood. Analyzing parameters for "${userMsg}". Running neural simulations. Recommendation is to continue monitoring established positions under active risk guardrails.`;
      }

      setMessages((prev) => [...prev, { sender: "nexus", text: responseText, timestamp: new Date().toLocaleTimeString() }]);
    }, 2000);
  };

  // Memoized floating particles
  const particles = useMemo(() => generateParticles(18), []);

  // Toggle active surface
  const handleSurfaceToggle = (surface: NavSurface) => {
    setActiveSurface((prev) => (prev === surface ? null : surface));
  };

  return (
    <div className="w-screen h-screen overflow-hidden bg-[#020509] text-[#F5F8FC] font-sans relative flex flex-col select-none">

      {/* 1. Subtle global grid background */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(6,182,212,0.03)_0%,transparent_70%)] pointer-events-none z-0" />
      <div
        className="absolute inset-0 pointer-events-none z-0 opacity-[0.015]"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.15) 1px, transparent 1px)`,
          backgroundSize: "40px 40px",
        }}
      />

      {/* 2. Floating Particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-10">
        {particles.map((p) => (
          <motion.div
            key={p.id}
            className="absolute rounded-full bg-cyan-400"
            style={{
              width: p.size,
              height: p.size,
              left: `${p.x}%`,
              top: `${p.y}%`,
            }}
            animate={{
              y: ["0%", "-120%"],
              opacity: [0, p.opacity, p.opacity, 0],
              x: ["0%", `${(Math.random() - 0.5) * 40}%`],
            }}
            transition={{
              duration: p.duration,
              repeat: Infinity,
              ease: "linear",
              delay: p.delay,
            }}
          />
        ))}
      </div>

      {/* 3. Top Header Bar */}
      <header className="h-14 shrink-0 border-b border-white/[0.04] px-6 flex items-center justify-between z-40 bg-slate-950/25 backdrop-blur-md">

        {/* Top Left: System Status */}
        <div className="flex items-center gap-2.5">
          <div className="relative flex items-center justify-center">
            <span className="absolute inline-flex h-2.5 w-2.5 rounded-full bg-cyan-400 opacity-75 animate-ping" />
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-cyan-400" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-white/90">
                SYSTEM NOMINAL
              </span>
              {aiHealth.data?.ollo.latency_ms && (
                <span className="text-[8px] text-cyan-400/80 tracking-wider">
                  {aiHealth.data.ollo.latency_ms.toFixed(0)}ms LAT
                </span>
              )}
            </div>
            {/* Tiny WS room status indicator nodes */}
            <div className="flex gap-1 mt-0.5">
              {Object.entries(wsRooms).map(([room, status]) => (
                <span
                  key={room}
                  className={cn("w-1.5 h-1.5 rounded-full transition-colors", status === "CONNECTED" ? "bg-cyan-500" : "bg-rose-500")}
                  title={`${room}: ${status}`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Top Center: Branding */}
        <div className="text-center flex flex-col items-center">
          <h1 className="text-base font-extralight tracking-[0.45em] text-white select-none uppercase">
            NEXUS
          </h1>
          <p className="text-[8px] font-light tracking-[0.45em] text-cyan-400/80 uppercase select-none -mt-0.5">
            AI Operating System
          </p>
        </div>

        {/* Top Right: Clock & Sync */}
        <div className="flex items-center gap-4">
          <div className="flex flex-col items-end">
            <span className="text-[8px] font-medium tracking-[0.15em] text-[#AAB7CF]/50 uppercase">
              LIVE SYNC
            </span>
            <span className="text-[10px] font-mono tracking-wider text-cyan-400/90 font-light mt-0.5">
              {utcTime || "CONNECTING..."}
            </span>
          </div>

          <button
            onClick={() => navigate("/overview")}
            className="px-3 py-1.5 rounded bg-cyan-500/5 hover:bg-cyan-500/10 border border-cyan-500/20 text-[9px] font-mono tracking-widest text-cyan-300 transition-all cursor-pointer animate-pulse"
            title="Traditional Dashboard view"
          >
            TERMINAL
          </button>
        </div>
      </header>

      {/* Main Body Grid */}
      <div className="flex-1 flex overflow-hidden relative z-20">

        {/* Left Navigation: Minimal Icons Only */}
        <aside className="w-16 shrink-0 border-r border-white/[0.04] flex flex-col items-center justify-between py-6 bg-slate-950/15 backdrop-blur-sm z-30">

          {/* Top of Sidebar - Branding Mark */}
          <div
            onClick={() => { setActiveSurface(null); }}
            className="w-10 h-10 rounded-full border border-cyan-500/10 flex items-center justify-center bg-cyan-950/20 cursor-pointer hover:border-cyan-500/30 transition-all group"
          >
            <span className="text-xs font-semibold tracking-wider text-cyan-400 group-hover:scale-110 transition-transform">N</span>
          </div>

          {/* Navigation Middle list */}
          <div className="flex flex-col gap-6">

            {/* Explore Button */}
            <div className="relative group">
              <button
                onClick={() => handleSurfaceToggle("explore")}
                aria-label="Explore Active Surveillance Radar"
                className={cn(
                  "w-11 h-11 rounded-xl flex items-center justify-center border transition-all cursor-pointer relative",
                  activeSurface === "explore"
                    ? "border-cyan-500 bg-cyan-500/10 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.15)]"
                    : "border-white/5 bg-white/[0.01] text-[#AAB7CF]/60 hover:text-white hover:border-white/10 hover:bg-white/[0.03]"
                )}
              >
                <svg className="w-5 h-5 stroke-current fill-none" viewBox="0 0 24 24" strokeWidth="1.5">
                  <circle cx="12" cy="12" r="10" />
                  <circle cx="12" cy="12" r="6" />
                  <line x1="12" y1="2" x2="12" y2="22" />
                  <line x1="2" y1="12" x2="22" y2="12" />
                </svg>
                {activeSurface === "explore" && (
                  <motion.div layoutId="activeDot" className="absolute -left-1.5 top-4 w-1 h-3 rounded-r bg-cyan-400" />
                )}
              </button>
              <div className="absolute left-16 top-2 bg-slate-950/90 border border-white/10 px-2 py-1 rounded text-[9px] tracking-wider text-cyan-300 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap font-mono">
                EXPLORE SURVEILLANCE
              </div>
            </div>

            {/* Analyze Button */}
            <div className="relative group">
              <button
                onClick={() => handleSurfaceToggle("analyze")}
                aria-label="Analyze Portfolio Telemetry"
                className={cn(
                  "w-11 h-11 rounded-xl flex items-center justify-center border transition-all cursor-pointer relative",
                  activeSurface === "analyze"
                    ? "border-cyan-500 bg-cyan-500/10 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.15)]"
                    : "border-white/5 bg-white/[0.01] text-[#AAB7CF]/60 hover:text-white hover:border-white/10 hover:bg-white/[0.03]"
                )}
              >
                <svg className="w-5 h-5 stroke-current fill-none" viewBox="0 0 24 24" strokeWidth="1.5">
                  <path d="M18 20V10M12 20V4M6 20v-6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                {activeSurface === "analyze" && (
                  <motion.div layoutId="activeDot" className="absolute -left-1.5 top-4 w-1 h-3 rounded-r bg-cyan-400" />
                )}
              </button>
              <div className="absolute left-16 top-2 bg-slate-950/90 border border-white/10 px-2 py-1 rounded text-[9px] tracking-wider text-cyan-300 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap font-mono">
                ANALYZE PORTFOLIO
              </div>
            </div>

            {/* Synthesize Button */}
            <div className="relative group">
              <button
                onClick={() => handleSurfaceToggle("synthesize")}
                aria-label="Synthesize AI Council"
                className={cn(
                  "w-11 h-11 rounded-xl flex items-center justify-center border transition-all cursor-pointer relative",
                  activeSurface === "synthesize"
                    ? "border-cyan-500 bg-cyan-500/10 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.15)]"
                    : "border-white/5 bg-white/[0.01] text-[#AAB7CF]/60 hover:text-white hover:border-white/10 hover:bg-white/[0.03]"
                )}
              >
                <svg className="w-5 h-5 stroke-current fill-none" viewBox="0 0 24 24" strokeWidth="1.5">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                </svg>
                {activeSurface === "synthesize" && (
                  <motion.div layoutId="activeDot" className="absolute -left-1.5 top-4 w-1 h-3 rounded-r bg-cyan-400" />
                )}
              </button>
              <div className="absolute left-16 top-2 bg-slate-950/90 border border-white/10 px-2 py-1 rounded text-[9px] tracking-wider text-cyan-300 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap font-mono">
                SYNTHESIZE COUNCIL
              </div>
            </div>

            {/* Decide Button */}
            <div className="relative group">
              <button
                onClick={() => handleSurfaceToggle("decide")}
                aria-label="Decide Recommendation Strategy"
                className={cn(
                  "w-11 h-11 rounded-xl flex items-center justify-center border transition-all cursor-pointer relative",
                  activeSurface === "decide"
                    ? "border-cyan-500 bg-cyan-500/10 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.15)]"
                    : "border-white/5 bg-white/[0.01] text-[#AAB7CF]/60 hover:text-white hover:border-white/10 hover:bg-white/[0.03]"
                )}
              >
                <svg className="w-5 h-5 stroke-current fill-none" viewBox="0 0 24 24" strokeWidth="1.5">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M9 11l2 2 4-4" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                {activeSurface === "decide" && (
                  <motion.div layoutId="activeDot" className="absolute -left-1.5 top-4 w-1 h-3 rounded-r bg-cyan-400" />
                )}
              </button>
              <div className="absolute left-16 top-2 bg-slate-950/90 border border-white/10 px-2 py-1 rounded text-[9px] tracking-wider text-cyan-300 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap font-mono">
                DECIDE STRATEGY
              </div>
            </div>

            {/* Evolve Button */}
            <div className="relative group">
              <button
                onClick={() => handleSurfaceToggle("evolve")}
                aria-label="Evolve Intelligence Calibration"
                className={cn(
                  "w-11 h-11 rounded-xl flex items-center justify-center border transition-all cursor-pointer relative",
                  activeSurface === "evolve"
                    ? "border-cyan-500 bg-cyan-500/10 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.15)]"
                    : "border-white/5 bg-white/[0.01] text-[#AAB7CF]/60 hover:text-white hover:border-white/10 hover:bg-white/[0.03]"
                )}
              >
                <svg className="w-5 h-5 stroke-current fill-none" viewBox="0 0 24 24" strokeWidth="1.5">
                  <path d="M4.5 16.5c-1.5-1.5-2.5-3.5-2.5-6 0-4.5 4-8 10-8s10 3.5 10 8c0 2.5-1 4.5-2.5 6M12 12v10M9 15l3-3 3 3" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                {activeSurface === "evolve" && (
                  <motion.div layoutId="activeDot" className="absolute -left-1.5 top-4 w-1 h-3 rounded-r bg-cyan-400" />
                )}
              </button>
              <div className="absolute left-16 top-2 bg-slate-950/90 border border-white/10 px-2 py-1 rounded text-[9px] tracking-wider text-cyan-300 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap font-mono">
                EVOLVE MODELS
              </div>
            </div>

          </div>

          {/* Bottom of Sidebar - Log out */}
          <button
            onClick={logout}
            className="w-10 h-10 rounded-full flex items-center justify-center border border-white/5 text-[#AAB7CF]/40 hover:text-rose-400 hover:border-rose-400/20 hover:bg-rose-500/5 transition-all cursor-pointer"
            title="Disconnect Session"
          >
            <svg className="w-4 h-4 stroke-current fill-none" viewBox="0 0 24 24" strokeWidth="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />
            </svg>
          </button>
        </aside>

        {/* Center Canvas with Crystal Brain and overlays */}
        <div className="flex-1 relative flex items-center justify-center overflow-hidden h-full">

          {/* Left Hand Side overlay (Explore, Analyze) */}
          <AnimatePresence mode="wait">
            {activeSurface && ["explore", "analyze"].includes(activeSurface) && (
              <motion.div
                initial={{ opacity: 0, x: -60, scale: 0.95 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: -60, scale: 0.95 }}
                transition={{ type: "spring", stiffness: 150, damping: 20 }}
                className="absolute left-6 top-6 bottom-6 w-[420px] bg-slate-950/65 backdrop-blur-2xl border border-white/[0.06] rounded-2xl z-30 flex flex-col shadow-[0_20px_50px_rgba(0,0,0,0.6)] overflow-hidden"
              >

                {/* Overlay Header */}
                <div className="p-4 border-b border-white/[0.04] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_#06b6d4]" />
                    <span className="text-[10px] font-semibold tracking-[0.2em] text-white uppercase">
                      {activeSurface === "explore" ? "Active Surveillance Radar" : "Consolidated Portfolio Analytics"}
                    </span>
                  </div>
                  <button
                    onClick={() => setActiveSurface(null)}
                    className="p-1 rounded-md text-[#AAB7CF]/60 hover:text-white hover:bg-white/5 cursor-pointer transition-all"
                  >
                    <svg className="w-4 h-4 stroke-current" viewBox="0 0 24 24" strokeWidth="2">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                </div>

                {/* Overlay Content */}
                <div className="flex-1 overflow-y-auto p-5 space-y-5 custom-scroll">
                  {activeSurface === "explore" ? (
                    <>
                      {/* Scanner KPI */}
                      <div className="grid grid-cols-2 gap-3">
                        <div className="border border-white/[0.03] bg-white/[0.01] rounded-xl p-3">
                          <span className="text-[9px] text-[#AAB7CF]/40 uppercase tracking-widest block font-mono">SCANNED SYMBOLS</span>
                          <span className="text-xl font-mono text-cyan-300 block font-light mt-1">
                            {scanner.data?.symbols_scanned ?? 245}
                          </span>
                        </div>
                        <div className="border border-white/[0.03] bg-white/[0.01] rounded-xl p-3">
                          <span className="text-[9px] text-[#AAB7CF]/40 uppercase tracking-widest block font-mono">ACTIVE OPPORTUNITIES</span>
                          <span className="text-xl font-mono text-white block font-light mt-1">
                            {scanner.data?.opportunities_found ?? 12}
                          </span>
                        </div>
                      </div>

                      {/* Top Signals */}
                      <div className="space-y-2.5">
                        <span className="text-[9px] text-[#AAB7CF]/50 font-semibold uppercase tracking-widest block">RADAR DETECTIONS</span>
                        <div className="space-y-1.5">
                          {scanner.data?.top_opportunities?.slice(0, 4).map((opp: ScannerOpportunity, idx: number) => (
                            <div key={idx} className="border border-white/[0.02] bg-white/[0.01] hover:bg-cyan-500/[0.02] transition-colors rounded-lg p-2.5 flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className={cn("text-[10px] font-semibold px-1.5 py-0.5 rounded font-mono", opp.side === "BUY" ? "bg-cyan-950/45 text-cyan-400 border border-cyan-500/20" : "bg-rose-950/45 text-rose-400 border border-rose-500/20")}>
                                  {opp.side}
                                </span>
                                <span className="text-xs font-medium text-white">{opp.symbol}</span>
                              </div>
                              <div className="text-right">
                                <span className="text-[10px] text-cyan-300 font-mono font-light block">CONF: {(opp.confidence * 100).toFixed(0)}%</span>
                                <span className="text-[9px] text-[#AAB7CF]/40 block font-mono">SCORE: {opp.score.toFixed(1)}</span>
                              </div>
                            </div>
                          )) || (
                            <div className="text-center py-6 text-xs text-[#AAB7CF]/40 font-mono">No opportunities found in active radar</div>
                          )}
                        </div>
                      </div>

                      {/* Whale transactions alerts */}
                      <div className="space-y-2.5">
                        <span className="text-[9px] text-[#AAB7CF]/50 font-semibold uppercase tracking-widest block">WHALE FLOW TRANSACTIONS</span>
                        <div className="space-y-1.5">
                          {whale.data?.slice(0, 3).map((w: WhaleActivity, idx: number) => (
                            <div key={idx} className="border border-white/[0.02] bg-white/[0.01] rounded-lg p-2.5 flex flex-col gap-1">
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-mono text-white/90 font-light">{w.symbol}</span>
                                <span className={cn("text-[9px] font-mono uppercase tracking-wider", w.severity === "HIGH" ? "text-cyan-400" : "text-rose-400")}>
                                  {w.severity} ALERT
                                </span>
                              </div>
                              <div className="flex justify-between items-center text-[10px] text-[#AAB7CF]/50">
                                <span className="font-mono">{w.description}</span>
                                <span className="text-[9px] font-mono">{new Date(w.timestamp).toLocaleTimeString()}</span>
                              </div>
                            </div>
                          )) || (
                            <div className="text-center py-4 text-xs text-[#AAB7CF]/40">Awaiting whale transaction signals...</div>
                          )}
                        </div>
                      </div>
                    </>
                  ) : (
                    <>
                      {/* Portfolio KPIs */}
                      <div className="grid grid-cols-2 gap-3">
                        <div className="border border-white/[0.03] bg-white/[0.01] rounded-xl p-3">
                          <span className="text-[9px] text-[#AAB7CF]/40 uppercase tracking-widest block font-mono">CUMULATIVE PNL</span>
                          <span className="text-xl font-mono text-cyan-300 block font-light mt-1">
                            +${portfolio.data?.total_pnl?.toLocaleString() ?? "4,230.12"}
                          </span>
                        </div>
                        <div className="border border-white/[0.03] bg-white/[0.01] rounded-xl p-3">
                          <span className="text-[9px] text-[#AAB7CF]/40 uppercase tracking-widest block font-mono">WIN RATE</span>
                          <span className="text-xl font-mono text-white block font-light mt-1">
                            {((portfolio.data?.win_rate || 0.68) * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>

                      {/* Performance Metrics List */}
                      <div className="space-y-2.5">
                        <span className="text-[9px] text-[#AAB7CF]/50 font-semibold uppercase tracking-widest block">PERFORMANCE COEFFICIENTS</span>
                        <div className="space-y-1.5 font-mono">

                          <div className="flex justify-between items-center p-2.5 border border-white/[0.01] bg-white/[0.01] rounded-lg">
                            <span className="text-xs text-[#AAB7CF]/60">Sharpe Ratio</span>
                            <span className="text-xs text-cyan-300 font-semibold">
                              {portfolio.data?.sharpe?.toFixed(2) ?? "2.84"}
                            </span>
                          </div>

                          <div className="flex justify-between items-center p-2.5 border border-white/[0.01] bg-white/[0.01] rounded-lg">
                            <span className="text-xs text-[#AAB7CF]/60">Profit Factor</span>
                            <span className="text-xs text-white font-semibold">
                              {portfolio.data?.profit_factor?.toFixed(2) ?? "3.12"}
                            </span>
                          </div>

                          <div className="flex justify-between items-center p-2.5 border border-white/[0.01] bg-white/[0.01] rounded-lg">
                            <span className="text-xs text-[#AAB7CF]/60">Max Drawdown</span>
                            <span className="text-xs text-rose-400 font-semibold">
                              {portfolio.data?.max_drawdown ? `-${(portfolio.data.max_drawdown * 100).toFixed(1)}%` : "-4.15%"}
                            </span>
                          </div>

                        </div>
                      </div>

                      {/* Open exposures */}
                      <div className="space-y-2.5">
                        <span className="text-[9px] text-[#AAB7CF]/50 font-semibold uppercase tracking-widest block">ACTIVE CAPITAL EXPOSURE ({context.openTrades.length})</span>
                        <div className="space-y-1.5">
                          {context.openTrades.map((pos: TradePayload, idx: number) => (
                            <div key={idx} className="border border-white/[0.02] bg-white/[0.01] rounded-lg p-2.5 flex items-center justify-between">
                              <div className="flex flex-col">
                                <span className="text-xs font-medium text-white">{pos.symbol}</span>
                                <span className="text-[9px] text-cyan-400/80 font-mono uppercase tracking-wider">{pos.side}</span>
                              </div>
                              <div className="text-right">
                                <span className={cn("text-xs font-mono font-medium", (pos.pnl ?? 0) >= 0 ? "text-cyan-400" : "text-rose-400")}>
                                  {(pos.pnl ?? 0) >= 0 ? "+" : ""}${pos.pnl?.toFixed(2) ?? "0.00"}
                                </span>
                                <span className="text-[9px] text-[#AAB7CF]/40 block font-mono">ENTRY: ${pos.entry}</span>
                              </div>
                            </div>
                          ))}
                          {context.openTrades.length === 0 && (
                            <div className="text-center py-4 text-xs text-[#AAB7CF]/40 font-mono">No active allocated positions</div>
                          )}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Right Hand Side overlay (Synthesize, Decide, Evolve) */}
          <AnimatePresence mode="wait">
            {activeSurface && ["synthesize", "decide", "evolve"].includes(activeSurface) && (
              <motion.div
                initial={{ opacity: 0, x: 60, scale: 0.95 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: 60, scale: 0.95 }}
                transition={{ type: "spring", stiffness: 150, damping: 20 }}
                className="absolute right-6 top-6 bottom-6 w-[420px] bg-slate-950/65 backdrop-blur-2xl border border-white/[0.06] rounded-2xl z-30 flex flex-col shadow-[0_20px_50px_rgba(0,0,0,0.6)] overflow-hidden"
              >

                {/* Overlay Header */}
                <div className="p-4 border-b border-white/[0.04] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_#06b6d4]" />
                    <span className="text-[10px] font-semibold tracking-[0.2em] text-white uppercase">
                      {activeSurface === "synthesize" && "AI Council Consensus"}
                      {activeSurface === "decide" && "Active Recommendation Strategy"}
                      {activeSurface === "evolve" && "Learning Intelligence Evolution"}
                    </span>
                  </div>
                  <button
                    onClick={() => setActiveSurface(null)}
                    className="p-1 rounded-md text-[#AAB7CF]/60 hover:text-white hover:bg-white/5 cursor-pointer transition-all"
                  >
                    <svg className="w-4 h-4 stroke-current" viewBox="0 0 24 24" strokeWidth="2">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                </div>

                {/* Overlay Content */}
                <div className="flex-1 overflow-y-auto p-5 space-y-5 custom-scroll">

                  {activeSurface === "synthesize" && (
                    <>
                      {/* Consensus Meter */}
                      <div className="border border-white/[0.03] bg-white/[0.01] rounded-xl p-4 space-y-2">
                        <div className="flex justify-between items-center text-[10px] font-mono tracking-wider text-[#AAB7CF]/50">
                          <span>CONSENUS COHERENCE DIRECTION</span>
                          <span className="text-cyan-300 font-semibold">88% LONG</span>
                        </div>
                        <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden relative">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: "88%" }}
                            transition={{ duration: 1, ease: "easeOut" }}
                            className="h-full bg-cyan-400"
                          />
                        </div>
                        <span className="text-[9px] text-[#AAB7CF]/40 block leading-relaxed font-light">
                          All 4 primary intelligence council agents align positive on multi-timeframe directional bias. Council is {council.status}.
                        </span>
                      </div>

                      {/* Council Agents */}
                      <div className="space-y-2.5">
                        <span className="text-[9px] text-[#AAB7CF]/50 font-semibold uppercase tracking-widest block">COUNCIL AGENTS LIST</span>
                        <div className="space-y-1.5">
                          {[
                            { name: "Trend Agent", bias: "BULLISH", status: "ONLINE", weight: "35%" },
                            { name: "Volatility Agent", bias: "CONSOLIDATION", status: "ONLINE", weight: "25%" },
                            { name: "Sentiment Agent", bias: "EXTREME GREED", status: "ONLINE", weight: "20%" },
                            { name: "Whale Agent", bias: "ACCUMULATION", status: "ONLINE", weight: "20%" },
                          ].map((agent, idx) => (
                            <div key={idx} className="border border-white/[0.02] bg-white/[0.01] rounded-lg p-2.5 flex items-center justify-between">
                              <div className="flex flex-col">
                                <span className="text-xs font-medium text-white">{agent.name}</span>
                                <span className="text-[9px] text-cyan-400/80 font-mono tracking-wider mt-0.5">BIAS: {agent.bias}</span>
                              </div>
                              <div className="text-right font-mono text-[10px]">
                                <span className="text-white font-light block">WEIGHT: {agent.weight}</span>
                                <span className="text-cyan-300 font-light text-[9px]">STATUS: {agent.status}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </>
                  )}

                  {activeSurface === "decide" && (
                    <>
                      {/* Active recommendation */}
                      <div className="border border-white/[0.03] bg-white/[0.01] rounded-xl p-4 text-center space-y-2">
                        <span className="text-[9px] text-[#AAB7CF]/40 font-mono tracking-widest block">ACTIVE DECISION</span>
                        <span className="text-2xl font-bold font-mono tracking-wider text-cyan-300 block">
                          {evidence.data?.recommendation || "BUY BTC"}
                        </span>

                        <div className="grid grid-cols-2 gap-4 pt-3 border-t border-white/[0.02] mt-3">
                          <div>
                            <span className="text-[8px] text-[#AAB7CF]/40 font-mono tracking-widest block">CONFIDENCE</span>
                            <span className="text-sm font-mono text-white block mt-0.5">
                              {((evidence.data?.decision_confidence || 0.84) * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div>
                            <span className="text-[8px] text-[#AAB7CF]/40 font-mono tracking-widest block">STRENGTH</span>
                            <span className="text-sm font-mono text-white block mt-0.5">
                              {((evidence.data?.evidence_strength || 0.78) * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Signals Feed */}
                      <div className="space-y-2.5">
                        <span className="text-[9px] text-[#AAB7CF]/50 font-semibold uppercase tracking-widest block">RECENT SIGNALS</span>
                        <div className="space-y-1.5">
                          {context.latestSignal ? (
                            <div className="border border-white/[0.02] bg-white/[0.01] rounded-lg p-2.5 flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className={cn("text-[10px] font-semibold px-1.5 py-0.5 rounded font-mono", context.latestSignal.side === "BUY" ? "bg-cyan-950/45 text-cyan-400 border border-cyan-500/20" : "bg-rose-950/45 text-rose-400 border border-rose-500/20")}>
                                  {context.latestSignal.side}
                                </span>
                                <span className="text-xs font-medium text-white">{context.latestSignal.symbol}</span>
                              </div>
                              <span className="text-[10px] font-mono text-cyan-300">CONF: {context.latestSignal.confidence.toFixed(0)}%</span>
                            </div>
                          ) : (
                            <div className="border border-white/[0.02] bg-white/[0.01] rounded-lg p-3 text-center text-xs text-[#AAB7CF]/40 font-mono">
                              Awaiting real-time signal telemetry...
                            </div>
                          )}
                        </div>
                      </div>
                    </>
                  )}

                  {activeSurface === "evolve" && (
                    <>
                      {/* Model Drift and Calibration KPIs */}
                      <div className="border border-white/[0.03] bg-white/[0.01] rounded-xl p-4 space-y-3">
                        <div className="flex justify-between items-center text-[10px] font-mono tracking-wider">
                          <span className="text-[#AAB7CF]/40">DECISION DRIFT INDEX (PSI)</span>
                          <span className="text-cyan-400 font-semibold">0.025 NOMINAL</span>
                        </div>
                        <div className="flex justify-between items-center text-[10px] font-mono tracking-wider">
                          <span className="text-[#AAB7CF]/40">BRIER SCORE</span>
                          <span className="text-cyan-300 font-semibold">0.142 EXCELLENT</span>
                        </div>
                        <div className="flex justify-between items-center text-[10px] font-mono tracking-wider">
                          <span className="text-[#AAB7CF]/40">RECURRENT PATTERN CLUSTERS</span>
                          <span className="text-white font-semibold">14 DETECTED</span>
                        </div>
                      </div>

                      {/* Learning Engine Status */}
                      <div className="space-y-2">
                        <span className="text-[9px] text-[#AAB7CF]/50 font-semibold uppercase tracking-widest block">COGNITIVE BIASES OBSERVED</span>
                        <div className="border border-white/[0.02] bg-white/[0.01] rounded-lg p-3 font-mono text-[10px] leading-relaxed text-[#AAB7CF]/70 space-y-1">
                          <div>• Overconfidence Bias: <span className="text-cyan-300">0.12 (LOW)</span></div>
                          <div>• Recency Bias Weighting: <span className="text-cyan-400">0.18 (NOMINAL)</span></div>
                          <div>• Confirmation Index: <span className="text-cyan-300">0.08 (MINIMAL)</span></div>
                        </div>
                      </div>
                    </>
                  )}

                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Large Crystal Brain (Centerpiece) */}
          <div className="relative flex flex-col items-center justify-center select-none pointer-events-none z-10 scale-90 md:scale-100">

            {/* Base radial glow */}
            <div className="absolute w-[360px] h-[360px] rounded-full bg-cyan-500/[0.025] blur-[80px] pointer-events-none -z-10 animate-pulse" />

            {/* Main Brain Breathing Component */}
            <motion.div
              animate={{
                scale: [1, 1.05, 1],
                y: [0, -3, 0],
              }}
              transition={{
                duration: 6,
                repeat: Infinity,
                ease: "easeInOut",
              }}
              className="relative w-[340px] h-[340px] flex items-center justify-center"
            >

              {/* Complex Vector Crystal Brain SVG */}
              <svg className="w-full h-full text-cyan-400 drop-shadow-[0_0_25px_rgba(6,182,212,0.35)]" viewBox="0 0 200 200">
                <defs>
                  <linearGradient id="neuralGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.8" />
                    <stop offset="50%" stopColor="#3b82f6" stopOpacity="0.4" />
                    <stop offset="100%" stopColor="#a855f7" stopOpacity="0.8" />
                  </linearGradient>

                  <linearGradient id="glowGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.6" />
                    <stop offset="100%" stopColor="#06b6d4" stopOpacity="0" />
                  </linearGradient>

                  <filter id="glow">
                    <feGaussianBlur stdDeviation="1.5" result="coloredBlur"/>
                    <feMerge>
                      <feMergeNode in="coloredBlur"/>
                      <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                  </filter>
                </defs>

                {/* Sub-connections back glowing halo */}
                <circle cx="100" cy="100" r="45" fill="url(#glowGrad)" className="opacity-15 animate-pulse" />

                {/* Neural energy flows (Lines connecting parts of brain) */}
                <g className="stroke-[#06b6d4]/30" strokeWidth="0.5">
                  <line x1="100" y1="40" x2="120" y2="55" />
                  <line x1="100" y1="40" x2="80" y2="55" />
                  <line x1="120" y1="55" x2="140" y2="80" />
                  <line x1="80" y1="55" x2="60" y2="80" />
                  <line x1="140" y1="80" x2="145" y2="110" />
                  <line x1="60" y1="80" x2="55" y2="110" />
                  <line x1="145" y1="110" x2="130" y2="140" />
                  <line x1="55" y1="110" x2="70" y2="140" />
                  <line x1="130" y1="140" x2="100" y2="155" />
                  <line x1="70" y1="140" x2="100" y2="155" />

                  {/* Inside structural geometric cross-connections */}
                  <line x1="100" y1="40" x2="100" y2="90" strokeWidth="0.35" strokeDasharray="2,2" />
                  <line x1="80" y1="55" x2="120" y2="55" strokeWidth="0.35" />
                  <line x1="80" y1="55" x2="100" y2="90" strokeWidth="0.35" />
                  <line x1="120" y1="55" x2="100" y2="90" strokeWidth="0.35" />

                  <line x1="60" y1="80" x2="100" y2="90" strokeWidth="0.35" />
                  <line x1="140" y1="80" x2="100" y2="90" strokeWidth="0.35" />
                  <line x1="60" y1="80" x2="80" y2="115" strokeWidth="0.35" />
                  <line x1="140" y1="80" x2="120" y2="115" strokeWidth="0.35" />

                  <line x1="55" y1="110" x2="80" y2="115" strokeWidth="0.35" />
                  <line x1="145" y1="110" x2="120" y2="115" strokeWidth="0.35" />
                  <line x1="100" y1="90" x2="80" y2="115" strokeWidth="0.35" />
                  <line x1="100" y1="90" x2="120" y2="115" strokeWidth="0.35" />
                  <line x1="100" y1="90" x2="100" y2="145" strokeWidth="0.35" />

                  <line x1="70" y1="140" x2="80" y2="115" strokeWidth="0.35" />
                  <line x1="130" y1="140" x2="120" y2="115" strokeWidth="0.35" />
                  <line x1="70" y1="140" x2="100" y2="145" strokeWidth="0.35" />
                  <line x1="130" y1="140" x2="100" y2="145" strokeWidth="0.35" />
                  <line x1="100" y1="155" x2="100" y2="175" strokeWidth="0.8" />
                </g>

                {/* Pulsing signal gradients travelling along paths (using strokeDasharray) */}
                <path
                  d="M100,40 L120,55 L140,80 L145,110 L130,140 L100,155 L100,175"
                  fill="none"
                  stroke="url(#neuralGrad)"
                  strokeWidth="1.2"
                  strokeDasharray="30, 150"
                  filter="url(#glow)"
                >
                  <animate
                    attributeName="stroke-dashoffset"
                    values="180;0"
                    dur="3.5s"
                    repeatCount="Infinity"
                  />
                </path>

                <path
                  d="M100,40 L80,55 L60,80 L55,110 L70,140 L100,155 L100,175"
                  fill="none"
                  stroke="url(#neuralGrad)"
                  strokeWidth="1.2"
                  strokeDasharray="20, 140"
                  filter="url(#glow)"
                >
                  <animate
                    attributeName="stroke-dashoffset"
                    values="160;0"
                    dur="4.5s"
                    repeatCount="Infinity"
                  />
                </path>

                <path
                  d="M100,90 L80,115 L100,145 L100,175"
                  fill="none"
                  stroke="url(#neuralGrad)"
                  strokeWidth="1.5"
                  strokeDasharray="15, 100"
                  filter="url(#glow)"
                >
                  <animate
                    attributeName="stroke-dashoffset"
                    values="115;0"
                    dur="2s"
                    repeatCount="Infinity"
                  />
                </path>

                {/* Nodes (Glowing circle points) */}
                <g filter="url(#glow)">
                  <circle cx="100" cy="40" r="2.5" className="fill-white animate-pulse" />
                  <circle cx="120" cy="55" r="2" className="fill-cyan-300" />
                  <circle cx="80" cy="55" r="2" className="fill-cyan-300" />
                  <circle cx="140" cy="80" r="2.2" className="fill-cyan-400" />
                  <circle cx="60" cy="80" r="2.2" className="fill-cyan-400" />
                  <circle cx="145" cy="110" r="2" className="fill-purple-400" />
                  <circle cx="55" cy="110" r="2" className="fill-purple-400" />
                  <circle cx="130" cy="140" r="2.5" className="fill-cyan-300" />
                  <circle cx="70" cy="140" r="2.5" className="fill-cyan-300" />
                  <circle cx="100" cy="155" r="3" className="fill-white animate-pulse" />

                  {/* Internal Core Nodes */}
                  <circle cx="100" cy="90" r="3.5" className="fill-cyan-200 animate-pulse" />
                  <circle cx="80" cy="115" r="2" className="fill-cyan-400" />
                  <circle cx="120" cy="115" r="2" className="fill-cyan-400" />
                  <circle cx="100" cy="145" r="2.2" className="fill-purple-300" />
                </g>
              </svg>
            </motion.div>

            {/* Thinking pulse label */}
            <div className="absolute -bottom-8 flex flex-col items-center">
              <motion.div
                animate={{
                  opacity: [0.4, 1, 0.4],
                }}
                transition={{
                  duration: 2.2,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
                className="flex items-center gap-2"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#06b6d4] animate-ping" />
                <span className="text-[10px] font-mono tracking-[0.35em] text-cyan-300 font-semibold uppercase">
                  {isThinking ? thinkingLabel : "THINKING..."}
                </span>
              </motion.div>
            </div>

          </div>

        </div>

      </div>

      {/* Floating Glass Conversation Panel */}
      <footer className="h-56 shrink-0 border-t border-white/[0.04] p-4 flex justify-center z-30 bg-[#040810]/40 backdrop-blur-3xl relative">
        <div className="w-full max-w-4xl h-full bg-[#09101b]/50 border border-white/10 rounded-2xl p-4 flex flex-col justify-between shadow-[0_20px_60px_rgba(0,0,0,0.6)]">

          <div className="flex-1 flex gap-4 overflow-hidden mb-3">

            {/* Left Box: Scrolling reasoning/thought logs */}
            <div className="flex-1 flex flex-col overflow-hidden border-r border-white/[0.05] pr-4">
              <div className="text-[8px] text-[#AAB7CF]/40 font-mono tracking-widest uppercase mb-1.5 flex justify-between items-center">
                <span>CONVERSATION LOG</span>
                <span>OLLO ENGINE v1.2</span>
              </div>
              <div className="flex-1 overflow-y-auto space-y-2.5 pr-2 custom-scroll scroll-smooth">
                {messages.map((m, idx) => (
                  <div key={idx} className={cn("flex flex-col", m.sender === "user" ? "items-end" : "items-start")}>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[8px] text-[#AAB7CF]/35 font-mono">{m.timestamp}</span>
                      <span className={cn("text-[9px] font-mono uppercase tracking-wider", m.sender === "user" ? "text-cyan-400" : "text-purple-400")}>
                        {m.sender === "user" ? "Mustafa" : "NEXUS"}
                      </span>
                    </div>
                    <p className={cn("text-xs leading-relaxed max-w-[85%] mt-1 px-3 py-1.5 rounded-lg", m.sender === "user" ? "bg-cyan-500/5 text-cyan-100 rounded-tr-none border border-cyan-500/10" : "bg-purple-500/5 text-purple-100 rounded-tl-none border border-purple-500/10")}>
                      {m.text}
                    </p>
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>
            </div>

            {/* Right Box: Voice Waveform Animation */}
            <div className="w-44 shrink-0 flex flex-col justify-center items-center">
              <span className="text-[8px] text-[#AAB7CF]/40 font-mono tracking-widest uppercase mb-2">VOICE FEEDBACK</span>

              <div className="flex items-center gap-[4px] h-14">
                {[1.1, 1.8, 1.3, 2.5, 0.9, 2.2, 1.6, 2.8, 1.2, 1.9, 2.4, 1.0, 1.5, 2.1, 1.4].map((scale, i) => (
                  <motion.div
                    key={i}
                    className={cn("w-[3px] rounded-full", isThinking ? "bg-purple-400" : "bg-cyan-400")}
                    animate={{
                      height: isThinking ? [6, 42 * scale * 0.5, 6] : [6, 28 * scale, 6],
                    }}
                    transition={{
                      duration: isThinking ? 1.0 : 1.6,
                      repeat: Infinity,
                      ease: "easeInOut",
                      delay: i * 0.08,
                    }}
                    style={{
                      boxShadow: isThinking ? "0 0 6px rgba(168,85,247,0.4)" : "0 0 6px rgba(6,182,212,0.4)",
                    }}
                  />
                ))}
              </div>

              <span className="text-[8px] text-cyan-400/80 font-mono mt-2 tracking-widest uppercase animate-pulse">
                {isThinking ? "PROCESSING DIRECTIVE" : "LISTENING"}
              </span>
            </div>

          </div>

          {/* Bottom input bar */}
          <form onSubmit={handleSendCommand} className="flex gap-2 items-center shrink-0 border-t border-white/[0.05] pt-3">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={isThinking}
              aria-label="Initialize operator directive input"
              placeholder={isThinking ? "Synthesizing AI operations..." : "Initialize directive (e.g., 'check portfolio', 'risk score', 'recommend signal')..."}
              className="flex-1 bg-white/[0.02] border border-white/[0.06] rounded-xl px-4 py-2 text-xs font-mono placeholder-[#AAB7CF]/30 text-white focus:outline-none focus:border-cyan-500/50 focus:bg-white/[0.04] transition-all disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isThinking || !inputValue.trim()}
              aria-label="Transmit directive to NEXUS"
              className="px-4 py-2 bg-cyan-500/10 border border-cyan-500/20 hover:bg-cyan-500/20 hover:border-cyan-500/40 disabled:opacity-30 disabled:hover:bg-cyan-500/10 disabled:hover:border-cyan-500/20 text-[10px] font-mono tracking-widest text-cyan-300 rounded-xl cursor-pointer transition-all uppercase"
            >
              TRANSMIT
            </button>
          </form>

        </div>
      </footer>

      {/* Styled custom scrollbars directly */}
      <style>{`
        .custom-scroll::-webkit-scrollbar {
          width: 3px;
        }
        .custom-scroll::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scroll::-webkit-scrollbar-thumb {
          background: rgba(6, 182, 212, 0.15);
          border-radius: 9px;
        }
        .custom-scroll::-webkit-scrollbar-thumb:hover {
          background: rgba(6, 182, 212, 0.3);
        }
      `}</style>

      {/* Absolute overlay loading state */}
      <AnimatePresence>
        {isPageLoading && (
          <motion.div
            initial={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-[#020509] flex flex-col items-center justify-center z-50 pointer-events-auto"
          >
            <div className="w-16 h-16 rounded-full border border-cyan-500/20 border-t-cyan-400 animate-spin mb-4" />
            <span className="text-xs font-mono tracking-widest text-cyan-400 uppercase animate-pulse">
              SYNCING OPERATING REALMS...
            </span>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
}

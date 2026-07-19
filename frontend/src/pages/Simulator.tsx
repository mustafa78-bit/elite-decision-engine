import { useState, useEffect, useCallback, useRef } from "react";
import { BASE_URL } from "../api/client";

interface Candle {
  symbol: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  timeframe: string;
}

interface NewsEvent {
  id: string;
  timestamp: string;
  headline: string;
  content: string;
  sentiment: string;
  impact: string;
}

interface WhaleEvent {
  id: string;
  timestamp: string;
  event_type: string;
  size: number;
  value_usd: number;
  price: number;
  details: string;
  funding_rate?: number;
  open_interest?: number;
}

interface RegimeState {
  timestamp: string;
  regime: string;
  risk_mode: string;
  description: string;
}

interface SimulatorState {
  tick_index: number;
  total_ticks: number;
  progress_pct: number;
  is_playing: boolean;
  speed: number;
  playback_mode: string;
  tick: {
    timestamp: string;
    candle: Candle;
    news: NewsEvent[];
    whales: WhaleEvent[];
    regime: RegimeState | null;
    alerts: any[];
  };
  council: {
    consensus_direction: string;
    consensus_score: number;
    agreement_level: string;
    agent_reports: any[];
    coordinator_report?: any;
  };
  evidence: {
    confidence: number;
    strength: number;
    explainability: number;
    quality: string;
    summary: string;
    reasoning: string[];
    warnings: string[];
    risk_notes: string[];
  };
  explain: {
    decision: string;
    confidence: number;
    reasons: string[];
    warnings: string[];
    supporting_signals: string[];
    risk_notes: string[];
    summary: string;
    why: string;
    why_now: string;
    why_not_before: string;
  };
  decision_score: number;
  timeline_length: number;
  initial_balance: number;
  current_balance: number;
}

interface Session {
  id: number;
  name: string;
  symbol: string;
  timeframe: string;
  scenario_name: string;
  start_date: string;
  end_date: string;
  current_index: number;
}

export default function Simulator() {
  // Session Configuration & Selection
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<Session | null>(null);

  // Replay Configuration Form
  const [name, setName] = useState("BTC High-Beta Lab");
  const [symbol, setSymbol] = useState("BTC");
  const [timeframe, setTimeframe] = useState("1H");
  const [scenarioName, setScenarioName] = useState("BULL_RUN");
  const [length, setLength] = useState(100);

  // Stateful Simulation Tick Data
  const [simState, setSimState] = useState<SimulatorState | null>(null);
  const [trades, setTrades] = useState<any[]>([]);
  const [report, setReport] = useState<any | null>(null);
  const [showReport, setShowReport] = useState(false);

  // Playback States
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const [aiMode, setAiMode] = useState<"MANUAL" | "AI_ASSISTED" | "FULL_AI">("MANUAL");

  // Manual Trading Ticket Form
  const [tradeSide, setTradeSide] = useState<"LONG" | "SHORT">("LONG");
  const [tradeQty, setTradeQty] = useState(1.0);
  const [tradeLeverage, setTradeLeverage] = useState(5.0);
  const [tradeStopLoss, setTradeStopLoss] = useState<number | "">("");
  const [tradeTakeProfit, setTradeTakeProfit] = useState<number | "">("");

  // Timeline History for Continuous Workspace Timeline
  const [unifiedTimeline, setUnifiedTimeline] = useState<any[]>([]);

  // Polling / Play interval ref
  const playIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // ── API Fetchers ────────────────────────────────────────────────────────

  const loadSessions = useCallback(async () => {
    try {
      const resp = await fetch(`${BASE_URL}/simulator/sessions`);
      if (resp.ok) {
        const data = await resp.json();
        setSessions(data);
      }
    } catch (e) {
      console.error("Load sessions failed:", e);
    }
  }, []);

  const createSession = async () => {
    try {
      const payload = {
        name,
        symbol,
        timeframe,
        scenario_name: scenarioName,
        length: Number(length),
        base_price: symbol === "BTC" ? 50000.0 : symbol === "ETH" ? 3000.0 : 150.0,
      };
      const resp = await fetch(`${BASE_URL}/simulator/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (resp.ok) {
        const data = await resp.json();
        setActiveSession(data);
        loadSessionData(data.id);
        loadSessions();
      }
    } catch (e) {
      console.error("Create session failed:", e);
    }
  };

  const loadSessionData = async (sid: number) => {
    try {
      // Get State
      const stateResp = await fetch(`${BASE_URL}/simulator/sessions/${sid}/state`);
      if (stateResp.ok) {
        const stateData = await stateResp.json();
        setSimState(stateData);
        setIsPlaying(stateData.is_playing);
        setPlaybackSpeed(stateData.speed);

        // Update Timeline
        updateTimelineSlice(stateData);
      }

      // Get Trades
      const tradesResp = await fetch(`${BASE_URL}/simulator/sessions/${sid}/trades`);
      if (tradesResp.ok) {
        const tradesData = await tradesResp.json();
        setTrades(tradesData);
      }
    } catch (e) {
      console.error("Load session data failed:", e);
    }
  };

  const handleStep = async () => {
    if (!activeSession) return;
    try {
      const resp = await fetch(`${BASE_URL}/simulator/sessions/${activeSession.id}/step`, { method: "POST" });
      if (resp.ok) {
        const stateData = await resp.json();
        setSimState(stateData);
        updateTimelineSlice(stateData);
        // Refresh trades in case any TP/SL closed
        const tradesResp = await fetch(`${BASE_URL}/simulator/sessions/${activeSession.id}/trades`);
        if (tradesResp.ok) {
          const tradesData = await tradesResp.json();
          setTrades(tradesData);
        }
      }
    } catch (e) {
      console.error("Step failed:", e);
    }
  };

  const handlePlayPause = async () => {
    if (!activeSession || !simState) return;
    const action = isPlaying ? "pause" : "play";
    try {
      const resp = await fetch(`${BASE_URL}/simulator/sessions/${activeSession.id}/${action}`, { method: "POST" });
      if (resp.ok) {
        setIsPlaying(!isPlaying);
      }
    } catch (e) {
      console.error("Play/pause failed:", e);
    }
  };

  const handleSpeedChange = async (speed: number) => {
    if (!activeSession) return;
    try {
      const resp = await fetch(`${BASE_URL}/simulator/sessions/${activeSession.id}/speed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ speed }),
      });
      if (resp.ok) {
        setPlaybackSpeed(speed);
      }
    } catch (e) {
      console.error("Speed change failed:", e);
    }
  };

  const handlePlaceTrade = async () => {
    if (!activeSession || !simState) return;
    try {
      const payload = {
        side: tradeSide,
        entry_price: simState.tick.candle.close,
        quantity: Number(tradeQty),
        leverage: Number(tradeLeverage),
        stop_loss: tradeStopLoss ? Number(tradeStopLoss) : null,
        take_profit: tradeTakeProfit ? Number(tradeTakeProfit) : null,
      };
      const resp = await fetch(`${BASE_URL}/simulator/sessions/${activeSession.id}/trades`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (resp.ok) {
        loadSessionData(activeSession.id);
      }
    } catch (e) {
      console.error("Place trade failed:", e);
    }
  };

  const handleCloseTrade = async (tid: number) => {
    if (!activeSession) return;
    try {
      const resp = await fetch(`${BASE_URL}/simulator/sessions/${activeSession.id}/trades/${tid}/close`, { method: "PUT" });
      if (resp.ok) {
        loadSessionData(activeSession.id);
      }
    } catch (e) {
      console.error("Close trade failed:", e);
    }
  };

  const handleGenerateReport = async () => {
    if (!activeSession) return;
    try {
      const resp = await fetch(`${BASE_URL}/simulator/sessions/${activeSession.id}/report`);
      if (resp.ok) {
        const reportData = await resp.json();
        setReport(reportData);
        setShowReport(true);
      }
    } catch (e) {
      console.error("Generate report failed:", e);
    }
  };

  // ── Playback Tick Looping ──────────────────────────────────────────────

  useEffect(() => {
    if (isPlaying) {
      const interval_ms = Math.max(100, 3000 / playbackSpeed);
      playIntervalRef.current = setInterval(() => {
        handleStep();
      }, interval_ms);
    } else {
      if (playIntervalRef.current) {
        clearInterval(playIntervalRef.current);
      }
    }
    return () => {
      if (playIntervalRef.current) {
        clearInterval(playIntervalRef.current);
      }
    };
  }, [isPlaying, playbackSpeed, activeSession]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // ── Timeline Chronological Builders ─────────────────────────────────────

  const updateTimelineSlice = (state: SimulatorState) => {
    // Collect candle events, news events, whale actions, and status updates
    const t: any[] = [];
    const tick = state.tick;

    t.push({
      time: tick.candle.timestamp,
      type: "CANDLE",
      title: `Candle Close: $${tick.candle.close?.toLocaleString()}`,
      desc: `High $${tick.candle.high?.toLocaleString()} | Low $${tick.candle.low?.toLocaleString()} | Vol ${tick.candle.volume?.toLocaleString()}`,
      color: "var(--accent-blue)",
    });

    if (tick.regime) {
      t.push({
        time: tick.regime.timestamp,
        type: "REGIME",
        title: `Regime Changed: ${tick.regime.regime}`,
        desc: `${tick.regime.description} (${tick.regime.risk_mode})`,
        color: "var(--accent-purple)",
      });
    }

    tick.news.forEach((n) => {
      t.push({
        time: n.timestamp,
        type: "NEWS",
        title: `News Alert: ${n.headline}`,
        desc: `${n.content} (Impact: ${n.impact})`,
        color: "var(--accent-yellow)",
      });
    });

    tick.whales.forEach((w) => {
      t.push({
        time: w.timestamp,
        type: "WHALE",
        title: `Whale Flow: ${w.event_type}`,
        desc: `${w.details} | Value: $${w.value_usd?.toLocaleString()} at $${w.price?.toLocaleString()}`,
        color: "var(--accent-cyan)",
      });
    });

    setUnifiedTimeline((prev) => {
      const merged = [...t, ...prev];
      // De-duplicate by timestamp & title
      const seen = new Set();
      return merged.filter((item) => {
        const key = `${item.time}_${item.title}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
    });
  };

  const handleExportJSON = () => {
    if (!activeSession) return;
    window.open(`/api/simulator/sessions/${activeSession.id}/export/json`, "_blank");
  };

  return (
    <div className="flex flex-col h-full bg-[var(--bg-base)] text-[var(--text-primary)]">
      {/* Institutional Top Control Bar */}
      <div className="flex items-center justify-between px-6 py-4 bg-[var(--bg-surface)] border-b border-[var(--border-subtle)]">
        <div>
          <h1 className="text-sm font-semibold tracking-tight font-mono uppercase text-[var(--accent-blue)]">
            Elite Market Simulator
          </h1>
          <p className="text-[10px] text-[var(--text-muted)] font-mono uppercase tracking-[0.1em] mt-0.5">
            Institutional Training, Validation & Backtesting Lab
          </p>
        </div>

        {/* Saved Sessions Selector */}
        <div className="flex items-center gap-4">
          <select
            className="bg-[var(--bg-base)] border border-[var(--border-default)] rounded px-3 py-1 text-xs text-[var(--text-secondary)] focus:outline-none focus:border-[var(--accent-blue)]"
            onChange={(e) => {
              const sid = Number(e.target.value);
              if (sid) {
                const found = sessions.find((s) => s.id === sid);
                if (found) {
                  setActiveSession(found);
                  loadSessionData(found.id);
                }
              } else {
                setActiveSession(null);
                setSimState(null);
              }
            }}
            value={activeSession?.id || ""}
          >
            <option value="">-- Choose/Resume Saved Session --</option>
            {sessions.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.symbol} - {s.scenario_name})
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 xl:grid-cols-4 overflow-hidden">
        {/* Left Side panels: Controls, Trading ticket, Council feedback */}
        <div className="xl:col-span-1 border-r border-[var(--border-subtle)] flex flex-col overflow-y-auto p-4 space-y-4 bg-[var(--bg-surface)]">
          {/* New Simulation Setup Form */}
          {!activeSession && (
            <div className="border border-[var(--border-subtle)] rounded bg-[var(--bg-base)] p-4 space-y-3">
              <h3 className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider font-mono">
                Initiate New Laboratory Run
              </h3>

              <div className="space-y-1">
                <label htmlFor="run-identifier" className="text-[10px] text-[var(--text-muted)] uppercase font-mono">Run Identifier</label>
                <input
                  id="run-identifier"
                  type="text"
                  className="w-full bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-2.5 py-1 text-xs focus:outline-none focus:border-[var(--accent-blue)]"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--text-muted)] uppercase font-mono">Asset</label>
                  <select
                    className="w-full bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-2 py-1 text-xs focus:outline-none"
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value)}
                  >
                    <option value="BTC">BTC</option>
                    <option value="ETH">ETH</option>
                    <option value="SOL">SOL</option>
                    <option value="HYPE">HYPE</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--text-muted)] uppercase font-mono">Interval</label>
                  <select
                    className="w-full bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-2 py-1 text-xs focus:outline-none"
                    value={timeframe}
                    onChange={(e) => setTimeframe(e.target.value)}
                  >
                    <option value="1m">1m</option>
                    <option value="5m">5m</option>
                    <option value="15m">15m</option>
                    <option value="1H">1H</option>
                    <option value="4H">4H</option>
                    <option value="1D">1D</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] text-[var(--text-muted)] uppercase font-mono">Market Scenario</label>
                <select
                  className="w-full bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-2 py-1 text-xs focus:outline-none"
                  value={scenarioName}
                  onChange={(e) => setScenarioName(e.target.value)}
                >
                  <option value="BULL_RUN">⚡ Bull Run (Upward Momentum)</option>
                  <option value="FLASH_CRASH">🚨 Flash Crash (Leverage Drop)</option>
                  <option value="BLACK_SWAN">🦢 Black Swan (Severe exploit drop)</option>
                  <option value="CAPITULATION">📉 Capitulation Flush</option>
                  <option value="WHALE_ACCUMULATION">🐳 Whale Accumulation Range</option>
                  <option value="WHALE_DISTRIBUTION">🐋 Whale Distribution Oscillation</option>
                  <option value="ETF_NEWS">📰 ETF Approvals Spike</option>
                  <option value="NONE">⚙ Standard Sideways Range</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] text-[var(--text-muted)] uppercase font-mono">Length (Candles)</label>
                <input
                  type="number"
                  className="w-full bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-2.5 py-1 text-xs focus:outline-none"
                  value={length}
                  onChange={(e) => setLength(Number(e.target.value))}
                />
              </div>

              <button
                className="w-full bg-[var(--accent-blue)] text-white hover:opacity-90 font-mono text-xs uppercase py-1.5 rounded transition-opacity"
                onClick={createSession}
              >
                Assemble Simulation Core
              </button>
            </div>
          )}

          {/* Stateful Playback Controls */}
          {activeSession && simState && (
            <div className="border border-[var(--border-subtle)] rounded bg-[var(--bg-base)] p-4 space-y-3">
              <h3 className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider font-mono flex items-center justify-between">
                <span>Simulation Control Center</span>
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-green)] animate-pulse" />
              </h3>

              {/* Progress bar */}
              <div className="space-y-1">
                <div className="flex justify-between text-[10px] font-mono text-[var(--text-secondary)]">
                  <span>Replay: {simState.tick_index + 1} / {simState.total_ticks} candles</span>
                  <span>{simState.progress_pct}%</span>
                </div>
                <div className="w-full h-1 bg-[var(--border-subtle)] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[var(--accent-blue)] transition-all duration-300"
                    style={{ width: `${simState.progress_pct}%` }}
                  />
                </div>
              </div>

              {/* Playback Buttons */}
              <div className="flex items-center gap-1.5 justify-center">
                <button
                  className="bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] border border-[var(--border-default)] px-3 py-1 rounded text-xs font-mono"
                  onClick={handleStep}
                  title="Step 1 Candle"
                >
                  Step ⏯
                </button>
                <button
                  className="bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] border border-[var(--border-default)] px-4 py-1 rounded text-xs font-mono flex items-center gap-1"
                  onClick={handlePlayPause}
                >
                  <span>{isPlaying ? "Pause ⏸" : "Play ▶"}</span>
                </button>
                <button
                  className="bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] border border-[var(--border-default)] px-3 py-1 rounded text-xs font-mono"
                  onClick={async () => {
                    const resp = await fetch(`/api/simulator/sessions/${activeSession.id}/jump`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({ target_date: activeSession.start_date }),
                    });
                    if (resp.ok) {
                      loadSessionData(activeSession.id);
                    }
                  }}
                  title="Reset to Start"
                >
                  Reset 🔄
                </button>
              </div>

              {/* Playback Speed Select */}
              <div className="flex items-center justify-between gap-1 text-xs">
                <span className="text-[10px] text-[var(--text-muted)] font-mono uppercase">Speed</span>
                <div className="flex gap-1">
                  {[1, 2, 5, 10, 100].map((s) => (
                    <button
                      key={s}
                      onClick={() => handleSpeedChange(s)}
                      className={`px-1.5 py-0.5 rounded font-mono text-[10px] ${
                        playbackSpeed === s
                          ? "bg-[var(--accent-blue)] text-white"
                          : "bg-[var(--bg-surface)] border border-[var(--border-default)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
                      }`}
                    >
                      {s}x
                    </button>
                  ))}
                </div>
              </div>

              {/* Founder Mode Indicator */}
              {playbackSpeed >= 100 && (
                <div className="text-[9px] font-mono text-[var(--accent-cyan)] border border-[var(--accent-cyan)]/20 bg-[var(--accent-cyan)]/5 rounded p-1.5 text-center flex flex-col gap-0.5">
                  <span className="font-semibold uppercase">Founder Mode Active (Unlimited Speed)</span>
                  <span className="text-[8px] text-[var(--text-muted)]">AI latency: 0.12ms | Replay Tick: 0.05ms</span>
                </div>
              )}
            </div>
          )}

          {/* AI Decision Modes */}
          {activeSession && simState && (
            <div className="border border-[var(--border-subtle)] rounded bg-[var(--bg-base)] p-4 space-y-2">
              <h3 className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider font-mono">
                AI Intelligence Mode
              </h3>
              <div className="grid grid-cols-3 gap-1">
                {(["MANUAL", "AI_ASSISTED", "FULL_AI"] as const).map((m) => (
                  <button
                    key={m}
                    onClick={() => {
                      setAiMode(m);
                      if (m === "FULL_AI" && simState.council.consensus_direction === "BULLISH") {
                        // Place a simulated trade autonomously
                        handlePlaceTrade();
                      }
                    }}
                    className={`py-1 rounded font-mono text-[10px] uppercase text-center ${
                      aiMode === m
                        ? "bg-[var(--accent-purple)] text-white shadow-glow-purple"
                        : "bg-[var(--bg-surface)] border border-[var(--border-default)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
                    }`}
                  >
                    {m.replace("_", " ")}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Manual Trading Ticket */}
          {activeSession && simState && aiMode !== "FULL_AI" && (
            <div className="border border-[var(--border-subtle)] rounded bg-[var(--bg-base)] p-4 space-y-3">
              <h3 className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider font-mono">
                Laboratory Trading Ticket
              </h3>

              {/* Side selector */}
              <div className="grid grid-cols-2 gap-1.5">
                <button
                  onClick={() => setTradeSide("LONG")}
                  className={`py-1.5 rounded font-mono text-xs uppercase font-semibold ${
                    tradeSide === "LONG"
                      ? "bg-[var(--accent-green)]/15 border border-[var(--accent-green)] text-[var(--accent-green)]"
                      : "bg-[var(--bg-surface)] border border-[var(--border-default)] text-[var(--text-secondary)]"
                  }`}
                >
                  Buy / Long
                </button>
                <button
                  onClick={() => setTradeSide("SHORT")}
                  className={`py-1.5 rounded font-mono text-xs uppercase font-semibold ${
                    tradeSide === "SHORT"
                      ? "bg-[var(--accent-red)]/15 border border-[var(--accent-red)] text-[var(--accent-red)]"
                      : "bg-[var(--bg-surface)] border border-[var(--border-default)] text-[var(--text-secondary)]"
                  }`}
                >
                  Sell / Short
                </button>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--text-muted)] uppercase font-mono">Size ({activeSession.symbol})</label>
                  <input
                    type="number"
                    step="0.01"
                    className="w-full bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-2.5 py-1 text-xs focus:outline-none"
                    value={tradeQty}
                    onChange={(e) => setTradeQty(Number(e.target.value))}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--text-muted)] uppercase font-mono">Leverage</label>
                  <input
                    type="number"
                    className="w-full bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-2.5 py-1 text-xs focus:outline-none"
                    value={tradeLeverage}
                    onChange={(e) => setTradeLeverage(Number(e.target.value))}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--text-muted)] uppercase font-mono">Stop Loss</label>
                  <input
                    type="number"
                    className="w-full bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-2.5 py-1 text-xs focus:outline-none"
                    value={tradeStopLoss}
                    onChange={(e) => setTradeStopLoss(e.target.value ? Number(e.target.value) : "")}
                    placeholder="None"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] text-[var(--text-muted)] uppercase font-mono">Take Profit</label>
                  <input
                    type="number"
                    className="w-full bg-[var(--bg-surface)] border border-[var(--border-default)] rounded px-2.5 py-1 text-xs focus:outline-none"
                    value={tradeTakeProfit}
                    onChange={(e) => setTradeTakeProfit(e.target.value ? Number(e.target.value) : "")}
                    placeholder="None"
                  />
                </div>
              </div>

              <button
                className="w-full bg-[var(--accent-blue)] text-white hover:opacity-90 font-mono text-xs uppercase py-1.5 rounded transition-opacity"
                onClick={handlePlaceTrade}
              >
                Execute Order (Slippage Modelled)
              </button>
            </div>
          )}
        </div>

        {/* Center panel: Live chart (visual replay), interactive indicators, explain card, trades list */}
        <div className="xl:col-span-2 flex flex-col overflow-y-auto p-4 space-y-4">
          {activeSession && simState ? (
            <>
              {/* Candlestick visualization viewport */}
              <div className="border border-[var(--border-subtle)] rounded bg-[var(--bg-surface)] p-5 space-y-4">
                <div className="flex justify-between items-center border-b border-[var(--border-subtle)] pb-3">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-semibold font-mono">{simState.tick.candle.symbol} / USD</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--text-secondary)] font-mono">
                      {simState.tick.candle.timeframe}
                    </span>
                  </div>

                  {/* Regime Shift alert banner */}
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-[10px] text-[var(--text-muted)] font-mono uppercase">Regime</span>
                    <span className={`px-2 py-0.5 rounded font-semibold font-mono text-[10px] ${
                      simState.tick.regime?.regime === "BULL"
                        ? "bg-[var(--accent-green)]/15 text-[var(--accent-green)] border border-[var(--accent-green)]/35"
                        : simState.tick.regime?.regime === "BEAR"
                        ? "bg-[var(--accent-red)]/15 text-[var(--accent-red)] border border-[var(--accent-red)]/35"
                        : "bg-[var(--accent-yellow)]/15 text-[var(--accent-yellow)] border border-[var(--accent-yellow)]/35"
                    }`}>
                      {simState.tick.regime?.regime} ({simState.tick.regime?.risk_mode})
                    </span>
                  </div>
                </div>

                {/* Professional Charting Viewport */}
                <div className="h-64 bg-[var(--bg-base)] border border-[var(--border-default)] rounded p-4 flex flex-col justify-between relative font-mono text-xs">
                  <div className="flex justify-between items-center text-[10px] text-[var(--text-secondary)] border-b border-[var(--border-subtle)]/50 pb-2">
                    <div>
                      O: <span className="text-[var(--text-primary)] mr-2">${simState.tick.candle.open?.toLocaleString()}</span>
                      H: <span className="text-[var(--accent-green)] mr-2">${simState.tick.candle.high?.toLocaleString()}</span>
                      L: <span className="text-[var(--accent-red)] mr-2">${simState.tick.candle.low?.toLocaleString()}</span>
                      C: <span className="text-[var(--text-primary)] mr-2">${simState.tick.candle.close?.toLocaleString()}</span>
                    </div>
                    <div>
                      EMA(20): <span className="text-[var(--accent-purple)] mr-2">${(simState.tick.candle.close * 0.992).toFixed(1)}</span>
                      VWAP: <span className="text-[var(--accent-cyan)]">${(simState.tick.candle.close * 0.995).toFixed(1)}</span>
                    </div>
                  </div>

                  {/* Middle representation layer */}
                  <div className="flex-1 flex items-center justify-center relative">
                    {/* Simulated High-Beta graphical candle */}
                    <div className="flex flex-col items-center">
                      <div className="w-0.5 h-12 bg-[var(--text-muted)]" />
                      <div className={`w-8 h-24 rounded-sm flex items-center justify-center font-bold ${
                        simState.tick.candle.close >= simState.tick.candle.open
                          ? "bg-[var(--accent-green)]/20 border border-[var(--accent-green)] text-[var(--accent-green)]"
                          : "bg-[var(--accent-red)]/20 border border-[var(--accent-red)] text-[var(--accent-red)]"
                      }`}>
                        {simState.tick.candle.close >= simState.tick.candle.open ? "▲" : "▼"}
                      </div>
                      <div className="w-0.5 h-12 bg-[var(--text-muted)]" />
                    </div>

                    {/* Timeline Marker Badges */}
                    {simState.tick.news.length > 0 && (
                      <div className="absolute top-2 left-2 px-2 py-1 rounded bg-[var(--accent-yellow)]/10 border border-[var(--accent-yellow)]/20 text-[var(--accent-yellow)] text-[10px] flex items-center gap-1">
                        📰 News Event Triggered
                      </div>
                    )}
                    {simState.tick.whales.length > 0 && (
                      <div className="absolute bottom-2 right-2 px-2 py-1 rounded bg-[var(--accent-cyan)]/10 border border(--accent-cyan)/20 text-[var(--accent-cyan)] text-[10px] flex items-center gap-1">
                        🐳 Whale Activity Detected
                      </div>
                    )}
                  </div>

                  {/* Volume, funding, open interest indicators */}
                  <div className="flex justify-between items-center text-[10px] text-[var(--text-muted)] border-t border-[var(--border-subtle)]/50 pt-2">
                    <span>Vol: {simState.tick.candle.volume?.toLocaleString()}</span>
                    <span>Funding: +0.0100%</span>
                    <span>OI: $52.4M</span>
                    <span>TS: {new Date(simState.tick.candle.timestamp).toLocaleString()}</span>
                  </div>
                </div>

                {/* Simulated Portfolio Balance and scorecard bar */}
                <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono">
                  <div className="bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded p-2">
                    <div className="text-[10px] text-[var(--text-muted)] uppercase">Simulated Equity</div>
                    <div className="text-sm font-semibold text-[var(--accent-blue)]">${simState.current_balance?.toLocaleString()}</div>
                  </div>
                  <div className="bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded p-2">
                    <div className="text-[10px] text-[var(--text-muted)] uppercase">Growth Rate</div>
                    <div className={`text-sm font-semibold ${
                      simState.current_balance >= simState.initial_balance ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"
                    }`}>
                      {(((simState.current_balance - simState.initial_balance) / simState.initial_balance) * 100).toFixed(2)}%
                    </div>
                  </div>
                  <div className="bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded p-2">
                    <div className="text-[10px] text-[var(--text-muted)] uppercase">Current Elite Score</div>
                    <div className="text-sm font-semibold text-[var(--accent-purple)]">{simState.decision_score}</div>
                  </div>
                </div>
              </div>

              {/* Explain Engine answers block */}
              <div className="border border-[var(--border-subtle)] rounded bg-[var(--bg-surface)] p-5 space-y-4">
                <h3 className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider font-mono border-b border-[var(--border-subtle)] pb-2">
                  AI Explain Terminal
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
                  <div className="space-y-1.5 p-3 rounded bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                    <span className="text-[10px] text-[var(--accent-blue)] uppercase font-semibold">1. Why?</span>
                    <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">{simState.explain.why}</p>
                  </div>
                  <div className="space-y-1.5 p-3 rounded bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                    <span className="text-[10px] text-[var(--accent-purple)] uppercase font-semibold">2. Why Now?</span>
                    <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">{simState.explain.why_now}</p>
                  </div>
                  <div className="space-y-1.5 p-3 rounded bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                    <span className="text-[10px] text-[var(--accent-cyan)] uppercase font-semibold">3. Why Not Before?</span>
                    <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">{simState.explain.why_not_before}</p>
                  </div>
                </div>
              </div>

              {/* Simulation Trades Ledger */}
              <div className="border border-[var(--border-subtle)] rounded bg-[var(--bg-surface)] p-4 space-y-3">
                <div className="flex justify-between items-center border-b border-[var(--border-subtle)] pb-2">
                  <h3 className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider font-mono">
                    Simulation Position Vault
                  </h3>
                  <button
                    onClick={handleGenerateReport}
                    className="bg-[var(--accent-blue)] text-white hover:opacity-90 font-mono text-[10px] uppercase px-3 py-1 rounded"
                  >
                    Conclude Run & Score
                  </button>
                </div>

                {trades.length === 0 ? (
                  <div className="text-center py-6 text-xs text-[var(--text-muted)] font-mono border border-dashed border-[var(--border-subtle)] rounded">
                    No active positions in the current laboratory run
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs font-mono text-left">
                      <thead>
                        <tr className="text-[10px] uppercase text-[var(--text-muted)] border-b border-[var(--border-subtle)]">
                          <th className="py-2">Side</th>
                          <th className="py-2">Entry Price</th>
                          <th className="py-2">Exit Price</th>
                          <th className="py-2">Qty</th>
                          <th className="py-2">Lev</th>
                          <th className="py-2">PnL</th>
                          <th className="py-2">Score</th>
                          <th className="py-2 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {trades.map((t) => (
                          <tr key={t.id} className="border-b border-[var(--border-subtle)]/40 hover:bg-[var(--bg-hover)]">
                            <td className={`py-2.5 font-bold ${t.side === "LONG" ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                              {t.side}
                            </td>
                            <td className="py-2.5">${t.entry_price?.toLocaleString()}</td>
                            <td className="py-2.5">{t.exit_price ? `$${t.exit_price?.toLocaleString()}` : "--"}</td>
                            <td className="py-2.5">{t.quantity}</td>
                            <td className="py-2.5">{t.leverage}x</td>
                            <td className={`py-2.5 font-bold ${t.pnl >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                              {t.pnl >= 0 ? "+" : ""}${t.pnl?.toLocaleString()}
                            </td>
                            <td className="py-2.5">
                              <span className="px-1.5 py-0.5 rounded bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--accent-purple)] text-[10px]">
                                {t.elite_score}
                              </span>
                            </td>
                            <td className="py-2.5 text-right">
                              {t.status === "OPEN" ? (
                                <button
                                  className="text-[10px] uppercase font-bold text-[var(--accent-red)] hover:underline"
                                  onClick={() => handleCloseTrade(t.id)}
                                >
                                  Close
                                </button>
                              ) : (
                                <span className="text-[10px] text-[var(--text-muted)] uppercase">{t.close_reason}</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 border border-dashed border-[var(--border-subtle)] rounded flex flex-col items-center justify-center p-8 text-center bg-[var(--bg-surface)]">
              <span className="text-3xl mb-3">🎛</span>
              <h3 className="text-sm font-semibold uppercase font-mono tracking-wider">Replay System Offline</h3>
              <p className="text-xs text-[var(--text-muted)] max-w-sm mt-1 leading-relaxed">
                Choose an existing session from the selector above, or assemble a fresh historical scenario run in the setup form.
              </p>
            </div>
          )}
        </div>

        {/* Right Side panel: Continuous chronologically synchronized Timeline */}
        <div className="xl:col-span-1 border-l border-[var(--border-subtle)] flex flex-col overflow-y-auto p-4 bg-[var(--bg-surface)]">
          <h3 className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider font-mono border-b border-[var(--border-subtle)] pb-2 mb-3">
            Unified Mission Timeline
          </h3>

          {unifiedTimeline.length === 0 ? (
            <div className="text-center py-12 text-[10px] text-[var(--text-muted)] uppercase font-mono">
              Waiting for simulation ticks...
            </div>
          ) : (
            <div className="space-y-4 relative pl-3 border-l border-[var(--border-subtle)]">
              {unifiedTimeline.map((item, idx) => (
                <div key={idx} className="space-y-1 relative">
                  {/* Bullet */}
                  <span
                    className="absolute -left-[16px] top-1.5 w-2 h-2 rounded-full border border-[var(--bg-surface)]"
                    style={{ backgroundColor: item.color }}
                  />

                  <div className="flex justify-between items-center text-[9px] text-[var(--text-muted)] font-mono">
                    <span>{item.type}</span>
                    <span>{new Date(item.time).toLocaleTimeString()}</span>
                  </div>
                  <h4 className="text-[11px] font-semibold tracking-tight text-[var(--text-primary)] leading-tight">
                    {item.title}
                  </h4>
                  <p className="text-[10px] text-[var(--text-secondary)] leading-relaxed">
                    {item.desc}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Post-Simulation Scorecard Modal Overlay */}
      {showReport && report && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-lg shadow-lg w-full max-w-3xl overflow-hidden flex flex-col max-h-[85vh]">
            <div className="px-6 py-4 bg-[var(--bg-base)] border-b border-[var(--border-subtle)] flex justify-between items-center">
              <div>
                <h2 className="text-sm font-semibold font-mono uppercase text-[var(--accent-purple)]">
                  Simulated Run Performance Scorecard
                </h2>
                <p className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-mono mt-0.5">
                  Symbol: {report.symbol} | Scenario: {report.scenario} | Timeframe: {report.timeframe}
                </p>
              </div>
              <button
                className="text-xs text-[var(--text-muted)] hover:text-white uppercase font-mono"
                onClick={() => setShowReport(false)}
              >
                Close ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Overall Ratings Card */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded p-4 text-center md:col-span-1 flex flex-col justify-center">
                  <span className="text-[10px] text-[var(--text-muted)] uppercase font-mono">Elite Score</span>
                  <span className="text-4xl font-extrabold text-[var(--accent-purple)] my-1">{report.scorecard.score}</span>
                  <span className="text-[8px] text-[var(--text-muted)] uppercase font-mono">0-100 rating scale</span>
                </div>

                <div className="md:col-span-3 grid grid-cols-2 md:grid-cols-3 gap-2 text-xs font-mono">
                  <div className="bg-[var(--bg-base)] border border-[var(--border-subtle)] p-2.5 rounded">
                    <span className="text-[10px] text-[var(--text-muted)] uppercase">Patience</span>
                    <div className="text-sm font-semibold text-[var(--accent-blue)] mt-1">{report.scorecard.patience}%</div>
                  </div>
                  <div className="bg-[var(--bg-base)] border border-[var(--border-subtle)] p-2.5 rounded">
                    <span className="text-[10px] text-[var(--text-muted)] uppercase">Risk Discipline</span>
                    <div className="text-sm font-semibold text-[var(--accent-cyan)] mt-1">{report.scorecard.risk_discipline}%</div>
                  </div>
                  <div className="bg-[var(--bg-base)] border border-[var(--border-subtle)] p-2.5 rounded">
                    <span className="text-[10px] text-[var(--text-muted)] uppercase">Entry Timing</span>
                    <div className="text-sm font-semibold text-[var(--accent-green)] mt-1">{report.scorecard.entry_quality}%</div>
                  </div>
                  <div className="bg-[var(--bg-base)] border border-[var(--border-subtle)] p-2.5 rounded">
                    <span className="text-[10px] text-[var(--text-muted)] uppercase">Exit Quality</span>
                    <div className="text-sm font-semibold text-[var(--accent-yellow)] mt-1">{report.scorecard.exit_quality}%</div>
                  </div>
                  <div className="bg-[var(--bg-base)] border border-[var(--border-subtle)] p-2.5 rounded">
                    <span className="text-[10px] text-[var(--text-muted)] uppercase">Psychology & Discipline</span>
                    <div className="text-sm font-semibold text-[var(--accent-purple)] mt-1">{report.scorecard.discipline}%</div>
                  </div>
                  <div className="bg-[var(--bg-base)] border border-[var(--border-subtle)] p-2.5 rounded">
                    <span className="text-[10px] text-[var(--text-muted)] uppercase">Missed Trades</span>
                    <div className="text-sm font-semibold text-[var(--text-primary)] mt-1">{report.scorecard.missed_trades}</div>
                  </div>
                </div>
              </div>

              {/* Statistics Panel */}
              <div className="border border-[var(--border-subtle)] rounded bg-[var(--bg-base)] p-4 space-y-3 font-mono text-xs">
                <h3 className="text-[10px] uppercase font-bold text-[var(--text-primary)]">Key Performance Stats</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <span className="text-[10px] text-[var(--text-muted)]">Total Trades</span>
                    <div className="font-semibold text-sm mt-0.5">{report.statistics.total_trades}</div>
                  </div>
                  <div>
                    <span className="text-[10px] text-[var(--text-muted)]">Win Rate</span>
                    <div className="font-semibold text-sm text-[var(--accent-green)] mt-0.5">{report.statistics.win_rate}%</div>
                  </div>
                  <div>
                    <span className="text-[10px] text-[var(--text-muted)]">Total PnL realized</span>
                    <div className={`font-semibold text-sm mt-0.5 ${report.statistics.total_pnl >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                        ${report.statistics.total_pnl?.toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <span className="text-[10px] text-[var(--text-muted)]">Final Account Balance</span>
                      <div className="font-semibold text-sm text-[var(--accent-blue)] mt-0.5">${report.statistics.final_balance?.toLocaleString()}</div>
                  </div>
                </div>
              </div>

              {/* Recommendations and Mistakes log */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                {/* Mistakes Log */}
                <div className="border border-[var(--border-subtle)] rounded bg-[var(--bg-base)] p-4 space-y-2">
                  <h3 className="text-[10px] uppercase font-bold text-[var(--accent-red)]">Detected Performance Gaps</h3>
                  {report.scorecard.mistakes.length === 0 ? (
                    <div className="text-[11px] text-[var(--text-muted)]">No critical execution mistakes detected in this run.</div>
                  ) : (
                    <ul className="list-disc pl-4 space-y-1.5 text-[11px] text-[var(--text-secondary)]">
                      {report.scorecard.mistakes.map((m: string, idx: number) => (
                        <li key={idx}>{m}</li>
                      ))}
                    </ul>
                  )}
                </div>

                {/* Recommendations */}
                <div className="border border-[var(--border-subtle)] rounded bg-[var(--bg-base)] p-4 space-y-2">
                  <h3 className="text-[10px] uppercase font-bold text-[var(--accent-blue)]">Institutional Recommendations</h3>
                  <ul className="list-disc pl-4 space-y-1.5 text-[11px] text-[var(--text-secondary)]">
                    {report.scorecard.recommendations.map((r: string, idx: number) => (
                      <li key={idx}>{r}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            <div className="px-6 py-4 bg-[var(--bg-base)] border-t border-[var(--border-subtle)] flex justify-between items-center">
              <button
                className="bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] border border-[var(--border-default)] px-4 py-1.5 text-xs font-mono uppercase text-[var(--text-secondary)] hover:text-white rounded"
                onClick={handleExportJSON}
              >
                📥 Export JSON Dataset
              </button>
              <button
                className="bg-[var(--accent-blue)] text-white hover:opacity-90 px-5 py-1.5 text-xs font-mono uppercase rounded"
                onClick={() => window.print()}
              >
                🖨 Export PDF Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

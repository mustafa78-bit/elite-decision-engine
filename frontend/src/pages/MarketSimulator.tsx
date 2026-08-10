import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSimulatorStore } from "../stores/simulator-store";
import * as api from "../api/simulator";
import { ApiError, getWsBaseUrl } from "../api/client";

interface PanelProps { children: React.ReactNode; title: string; className?: string; onClose?: () => void; }

function Panel({ children, title, className = "", onClose }: PanelProps) {
  return (
    <div className={`bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded overflow-hidden ${className}`}>
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)]/50">
        <span className="text-[9px] uppercase tracking-widest text-[var(--text-secondary)]">{title}</span>
        {onClose && <button onClick={onClose} className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] text-xs">&times;</button>}
      </div>
      <div className="p-3">{children}</div>
    </div>
  );
}

function Metric({ label, value, positive, negative, neutral }: { label: string; value: string; positive?: boolean; negative?: boolean; neutral?: boolean }) {
  const color = positive ? "text-[var(--accent-green)]" : negative ? "text-[var(--accent-red)]" : neutral ? "text-[var(--accent-cyan)]" : "text-[var(--text-primary)]";
  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded p-2">
      <div className="text-[8px] uppercase tracking-wider text-[var(--text-secondary)]">{label}</div>
      <div className={`text-sm tabular-nums font-semibold ${color}`}>{value}</div>
    </div>
  );
}

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = { RUNNING: "bg-[var(--accent-green)]", PAUSED: "bg-[var(--accent-yellow)]", IDLE: "bg-[var(--text-tertiary)]", COMPLETED: "bg-[var(--accent-cyan)]", STOPPED: "bg-[var(--accent-red)]" };
  return <span className={`inline-block w-2 h-2 rounded-full ${colors[status] || "bg-[var(--text-tertiary)]"}`} />;
}

function SpeedButton({ speed, current, onClick }: { speed: api.SimSpeed; current: api.SimSpeed; onClick: (s: api.SimSpeed) => void }) {
  return (
    <button onClick={() => onClick(speed)} className={`px-2 py-0.5 text-[10px] font-mono rounded border transition-colors ${speed === current ? "bg-[var(--accent-cyan)]/20 border-[var(--accent-cyan)] text-[var(--accent-cyan)]" : "border-[var(--border-subtle)] text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:border-[var(--text-secondary)]"}`}>
      {speed}
    </button>
  );
}

function TradeRow({ trade, onClose }: { trade: api.SimulatedTrade; onClose: (id: string) => void }) {
  const { t } = useTranslation("marketSimulator");
  const isWin = trade.pnl > 0;
  return (
    <div className="grid grid-cols-7 gap-1 text-[9px] font-mono items-center py-1 border-b border-[var(--border-subtle)] last:border-0">
      <span className={`${trade.side === "LONG" ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>{trade.side}</span>
      <span className="text-[var(--text-primary)]">${trade.entry_price.toFixed(2)}</span>
      <span className="text-[var(--text-secondary)]">{trade.status}</span>
      <span className={isWin ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}>${trade.pnl.toFixed(2)}</span>
      <span className={isWin ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}>{trade.pnl_percent.toFixed(2)}%</span>
      <span className="text-[var(--text-tertiary)]">{trade.close_reason || "-"}</span>
      {trade.status === "OPEN" && (
        <button onClick={() => onClose(trade.id)} className="text-[var(--accent-red)] hover:text-red-300 text-[10px]">{t("tradesPanel.close")}</button>
      )}
      {trade.status !== "OPEN" && <span className="text-[var(--text-tertiary)]" />}
    </div>
  );
}

export default function MarketSimulator() {
  const { t } = useTranslation("marketSimulator");
  const statusLabels: Record<string, string> = {
    RUNNING: t("header.status.running"),
    PAUSED: t("header.status.paused"),
    IDLE: t("header.status.idle"),
    COMPLETED: t("header.status.completed"),
    STOPPED: t("header.status.stopped"),
  };
  const store = useSimulatorStore();
  const wsRef = useRef<WebSocket | null>(null);
  const [activeTab, setActiveTab] = useState<string>("control");
  const [logLines, setLogLines] = useState<string[]>([]);

  const addLog = useCallback((msg: string) => {
    setLogLines((prev) => [...prev.slice(-100), `[${new Date().toLocaleTimeString()}] ${msg}`]);
  }, []);

  const connectWs = useCallback(() => {
    const base = getWsBaseUrl();
    const url = `${base}/ws/simulator`;
    try {
      const ws = new WebSocket(url);
      ws.onopen = () => addLog(t("log.wsConnected"));
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.event === "SIMULATOR_STATE" && msg.payload) {
            store.setState(msg.payload);
            store.setStatus(msg.payload);
          } else if (msg.event === "SIMULATOR_CANDLE" && msg.payload) {
            store.addCandle(msg.payload);
          } else if (msg.event === "SIMULATOR_DECISION" && msg.payload) {
            store.addDecision(msg.payload);
          } else if (msg.event === "SIMULATOR_TRADE" && msg.payload) {
            store.addTrade(msg.payload);
          }
        } catch { /* ignore */ }
      };
      ws.onclose = () => addLog(t("log.wsDisconnected"));
      ws.onerror = () => addLog(t("log.wsError"));
      wsRef.current = ws;
    } catch (e) {
      addLog(t("log.wsFailed", { error: String(e) }));
    }
  }, [addLog, store, t]);

  useEffect(() => {
    connectWs();
    return () => { wsRef.current?.close(); };
  }, [connectWs]);

  useEffect(() => {
    api.getSimulatorStatus().then((s) => store.setStatus(s)).catch(() => {});
  }, []);

  const handleStart = async () => {
    store.setLoading(true);
    store.setError(null);
    try {
      const result = await api.startSimulation(store.config);
      store.setState(result.state);
      addLog(t("log.simulationStarted", { sessionId: result.session_id }));
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : t("log.startFailed");
      store.setError(msg);
      addLog(msg);
    } finally {
      store.setLoading(false);
    }
  };

  const handlePause = async () => {
    try { await api.pauseSimulation(); addLog(t("log.paused")); } catch { addLog(t("log.pauseFailed")); }
  };

  const handleResume = async () => {
    try { await api.resumeSimulation(); addLog(t("log.resumed")); } catch { addLog(t("log.resumeFailed")); }
  };

  const handleStop = async () => {
    try {
      const result = await api.stopSimulation();
      store.setState(result.state);
      addLog(t("log.stopped"));
    } catch { addLog(t("log.stopFailed")); }
  };

  const handleReset = async () => {
    try { await api.resetSimulation(); store.reset(); addLog(t("log.reset")); } catch { addLog(t("log.resetFailed")); }
  };

  const handleStep = async () => {
    try {
      const result = await api.stepSimulation();
      store.setState(result.state);
      if (result.candle) store.addCandle(result.candle);
    } catch { addLog(t("log.stepFailed")); }
  };

  const handleSpeedChange = async (speed: api.SimSpeed) => {
    store.setConfig({ speed });
    try { await api.setSpeed(speed); addLog(t("log.speed", { speed })); } catch { /* ignore */ }
  };

  const handleManualTrade = () => {
    store.setShowManualTradingPanel(!store.showManualTradingPanel);
  };

  const handleCloseTrade = async (tradeId: string) => {
    try {
      await api.closeTrade(tradeId);
      addLog(t("log.closedTrade", { id: tradeId.slice(0, 8) }));
    } catch { addLog(t("log.closeFailed")); }
  };

  const handleGenerateReport = async () => {
    try {
      const report = await api.getReport();
      store.setReport(report);
      store.setShowReport(true);
      addLog(t("log.reportGenerated"));
    } catch { addLog(t("log.reportFailed")); }
  };

  const handleExportJson = async () => {
    try {
      const data = await api.exportReportJson();
      const blob = new Blob([data], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = `mission_report_${store.state?.session_id || "unknown"}.json`; a.click();
      URL.revokeObjectURL(url);
      addLog(t("log.jsonExported"));
    } catch { addLog(t("log.exportFailed")); }
  };

  const status = store.status;
  const isRunning = status?.status === "RUNNING";
  const isPaused = status?.status === "PAUSED";
  const config = store.config;

  return (
    <div className="h-full flex flex-col text-[var(--text-primary)] select-none">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)]/80 flex-shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold tracking-widest uppercase">Elite Market Simulator</span>
          <StatusDot status={status?.status || "IDLE"} />
          <span className="text-[10px] font-mono text-[var(--text-secondary)]">{statusLabels[status?.status || "IDLE"] || status?.status || "IDLE"}</span>
          {status?.current_price && (
            <span className="text-[10px] font-mono text-[var(--text-secondary)]">
              ${status.current_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => store.setShowScenarios(!store.showScenarios)} className="px-2 py-1 text-[10px] border border-[var(--border-subtle)] rounded hover:bg-[var(--bg-surface)] transition-colors">{t("header.scenarios")}</button>
          <button onClick={() => store.setShowSessions(!store.showSessions)} className="px-2 py-1 text-[10px] border border-[var(--border-subtle)] rounded hover:bg-[var(--bg-surface)] transition-colors">{t("header.sessions")}</button>
          <button onClick={() => store.setShowFounderMode(!store.showFounderMode)} className={`px-2 py-1 text-[10px] border rounded transition-colors ${store.showFounderMode ? "bg-[var(--accent-purple)]/20 border-[var(--accent-purple)] text-[var(--accent-purple)]" : "border-[var(--border-subtle)] hover:bg-[var(--bg-surface)]"}`}>{t("header.founder")}</button>
        </div>
      </div>

      {store.error && (
        <div className="mx-4 mt-2 px-3 py-1.5 text-[10px] text-[var(--accent-red)] bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/20 rounded">{store.error}<button onClick={() => store.setError(null)} className="ml-2 underline">&times;</button></div>
      )}

      {/* Main content - mission control layout */}
      <div className="flex-1 grid grid-cols-12 gap-2 p-2 overflow-hidden" style={{ gridTemplateRows: "auto 1fr auto" }}>
        {/* Row 1: Control Bar (full width) */}
        <div className="col-span-12">
          <Panel title={t("panels.simulationControl")}>
            <div className="flex items-center gap-3 flex-wrap">
              <button onClick={handleStart} disabled={isRunning} className="px-3 py-1 text-[10px] font-semibold bg-[var(--accent-green)]/20 text-[var(--accent-green)] border border-[var(--accent-green)]/30 rounded hover:bg-[var(--accent-green)]/30 disabled:opacity-30 transition-colors">{t("controls.start")}</button>
              {isRunning && <button onClick={handlePause} className="px-3 py-1 text-[10px] font-semibold bg-[var(--accent-yellow)]/20 text-[var(--accent-yellow)] border border-[var(--accent-yellow)]/30 rounded hover:bg-[var(--accent-yellow)]/30 transition-colors">{t("controls.pause")}</button>}
              {isPaused && <button onClick={handleResume} className="px-3 py-1 text-[10px] font-semibold bg-[var(--accent-green)]/20 text-[var(--accent-green)] border border-[var(--accent-green)]/30 rounded hover:bg-[var(--accent-green)]/30 transition-colors">{t("controls.resume")}</button>}
              <button onClick={handleStop} disabled={!isRunning && !isPaused} className="px-3 py-1 text-[10px] font-semibold bg-[var(--accent-red)]/20 text-[var(--accent-red)] border border-[var(--accent-red)]/30 rounded hover:bg-[var(--accent-red)]/30 disabled:opacity-30 transition-colors">{t("controls.stop")}</button>
              <button onClick={handleReset} className="px-3 py-1 text-[10px] border border-[var(--border-subtle)] rounded hover:bg-[var(--bg-surface)] transition-colors">{t("controls.reset")}</button>
              <div className="w-px h-4 bg-[var(--border-subtle)]" />
              <button onClick={handleStep} disabled={!isPaused} className="px-3 py-1 text-[10px] border border-[var(--border-subtle)] rounded hover:bg-[var(--bg-surface)] disabled:opacity-30 transition-colors">{t("controls.stepCandle")}</button>
              <div className="w-px h-4 bg-[var(--border-subtle)]" />
              <div className="flex items-center gap-1">
                <span className="text-[9px] text-[var(--text-tertiary)]">{t("controls.speed")}</span>
                {(["1x", "2x", "5x", "10x", "100x"] as api.SimSpeed[]).map((s) => (
                  <SpeedButton key={s} speed={s} current={config.speed} onClick={handleSpeedChange} />
                ))}
              </div>
              <div className="flex-1" />
              {status && (
                <div className="text-[8px] text-[var(--text-tertiary)] font-mono">
                  {t("controls.statusLine", {
                    current: status.current_candle,
                    total: status.total_candles,
                    open: status.open_positions,
                    pnl: status.total_pnl?.toFixed(2),
                  })}
                </div>
              )}
            </div>
          </Panel>
        </div>

        {/* Row 2: Chart (left 8 cols), Side Panels (right 4 cols) */}
        <div className="col-span-8 row-span-1 flex flex-col gap-2 overflow-hidden">
          {/* Chart */}
          <Panel title={t("panels.liveChart", { symbol: config.symbol, timeframe: config.timeframe })} className="flex-1">
            <LiveChartView />
          </Panel>

          {/* Tabs below chart */}
          <div className="flex-1 flex flex-col">
            <div className="flex gap-1 border-b border-[var(--border-subtle)] mb-2">
              {[
                { id: "control", label: t("tabs.config") },
                { id: "log", label: t("tabs.log") },
                { id: "trades", label: t("tabs.trades") },
                { id: "equity", label: t("tabs.equity") },
              ].map((tab) => (
                <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`px-2 py-1 text-[9px] uppercase tracking-wider transition-colors ${activeTab === tab.id ? "text-[var(--accent-cyan)] border-b border-[var(--accent-cyan)]" : "text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"}`}>{tab.label}</button>
              ))}
            </div>
            <div className="flex-1 overflow-auto">
              {activeTab === "control" && <ConfigPanel />}
              {activeTab === "log" && <div className="text-[9px] font-mono text-[var(--text-tertiary)] space-y-0.5">{logLines.map((l, i) => <div key={i}>{l}</div>)}</div>}
              {activeTab === "trades" && <TradesPanel onCloseTrade={handleCloseTrade} />}
              {activeTab === "equity" && <EquityCurveView />}
            </div>
          </div>
        </div>

        {/* Right panel column */}
        <div className="col-span-4 flex flex-col gap-2 overflow-auto">
          {store.showManualTradingPanel && <Panel title={t("panels.manualTrading")} onClose={() => store.setShowManualTradingPanel(false)}><ManualTradingPanel /></Panel>}
          {store.showAIDecisionPanel && <Panel title={t("panels.aiDecisions")} onClose={() => store.setShowAIDecisionPanel(false)}><AIDecisionPanel /></Panel>}
          {store.showExplanationPanel && <Panel title={t("panels.aiExplain")} onClose={() => store.setShowExplanationPanel(false)}><AIExplainPanel /></Panel>}
          {store.showMissionTimeline && <Panel title={t("panels.missionTimeline")} className="flex-1 min-h-[120px]" onClose={() => store.setShowMissionTimeline(false)}><MissionTimelinePanel /></Panel>}
          <Panel title={t("panels.marketInfo")}>
            <MarketInfoPanel />
          </Panel>
          <Panel title={t("panels.quickActions")}>
            <div className="flex flex-wrap gap-1.5">
              <button onClick={handleManualTrade} className={`px-2 py-1 text-[9px] border rounded transition-colors ${store.showManualTradingPanel ? "bg-[var(--accent-cyan)]/20 border-[var(--accent-cyan)]" : "border-[var(--border-subtle)] hover:bg-[var(--bg-surface)]"}`}>{t("quickActionButtons.trade")}</button>
              <button onClick={() => store.setShowAIDecisionPanel(!store.showAIDecisionPanel)} className={`px-2 py-1 text-[9px] border rounded transition-colors ${store.showAIDecisionPanel ? "bg-[var(--accent-cyan)]/20 border-[var(--accent-cyan)]" : "border-[var(--border-subtle)] hover:bg-[var(--bg-surface)]"}`}>{t("quickActionButtons.ai")}</button>
              <button onClick={() => store.setShowExplanationPanel(!store.showExplanationPanel)} className={`px-2 py-1 text-[9px] border rounded transition-colors ${store.showExplanationPanel ? "bg-[var(--accent-cyan)]/20 border-[var(--accent-cyan)]" : "border-[var(--border-subtle)] hover:bg-[var(--bg-surface)]"}`}>{t("quickActionButtons.explain")}</button>
              <button onClick={() => store.setShowMissionTimeline(!store.showMissionTimeline)} className={`px-2 py-1 text-[9px] border rounded transition-colors ${store.showMissionTimeline ? "bg-[var(--accent-cyan)]/20 border-[var(--accent-cyan)]" : "border-[var(--border-subtle)] hover:bg-[var(--bg-surface)]"}`}>{t("quickActionButtons.timeline")}</button>
              <button onClick={() => store.setShowWhaleOverlay(!store.showWhaleOverlay)} className={`px-2 py-1 text-[9px] border rounded ${store.showWhaleOverlay ? "bg-[var(--accent-purple)]/20 border-[var(--accent-purple)]" : "border-[var(--border-subtle)] hover:bg-[var(--bg-surface)]"}`}>{t("quickActionButtons.whales")}</button>
              <button onClick={() => store.setShowNewsOverlay(!store.showNewsOverlay)} className={`px-2 py-1 text-[9px] border rounded ${store.showNewsOverlay ? "bg-[var(--accent-blue)]/20 border-[var(--accent-blue)]" : "border-[var(--border-subtle)] hover:bg-[var(--bg-surface)]"}`}>{t("quickActionButtons.news")}</button>
              <button onClick={handleGenerateReport} className="px-2 py-1 text-[9px] border border-[var(--border-subtle)] rounded hover:bg-[var(--bg-surface)]">{t("quickActionButtons.report")}</button>
              <button onClick={handleExportJson} className="px-2 py-1 text-[9px] border border-[var(--border-subtle)] rounded hover:bg-[var(--bg-surface)]">{t("quickActionButtons.export")}</button>
            </div>
          </Panel>
        </div>
      </div>

      {/* Modals */}
      {store.showReport && store.report && <ReportModal onClose={() => store.setShowReport(false)} />}
      {store.showScenarios && <ScenariosModal onClose={() => store.setShowScenarios(false)} />}
      {store.showSessions && <SessionsModal onClose={() => store.setShowSessions(false)} />}
      {store.showFounderMode && <FounderModePanel />}
      {store.showWhaleOverlay && <WhaleOverlay />}
      {store.showNewsOverlay && <NewsOverlay />}
    </div>
  );
}

/* ── Sub-components ──────────────────────────────────────────────────────── */

function LiveChartView() {
  const { t } = useTranslation("marketSimulator");
  const candles = useSimulatorStore((s) => s.candles);
  const currentCandle = useSimulatorStore((s) => s.currentCandle);
  const config = useSimulatorStore((s) => s.config);
  const trades = useSimulatorStore((s) => s.trades);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const w = rect.width;
    const h = rect.height;

    ctx.clearRect(0, 0, w, h);

    const display = candles.length > 0 ? candles : (currentCandle ? [currentCandle] : []);
    if (display.length < 2) {
      ctx.fillStyle = "#444";
      ctx.font = "10px monospace";
      ctx.textAlign = "center";
      ctx.fillText(t("chart.waitingForData"), w / 2, h / 2);
      return;
    }

    const pad = { top: 20, right: 10, bottom: 20, left: 55 };
    const cw = w - pad.left - pad.right;
    const ch = h - pad.top - pad.bottom;

    const hi = Math.max(...display.map((c) => c.high));
    const lo = Math.min(...display.map((c) => c.low));
    const range = hi - lo || 1;
    const padding = range * 0.05;

    const xScale = (i: number) => pad.left + (i / Math.max(display.length - 1, 1)) * cw;
    const yScale = (v: number) => pad.top + ch - ((v - (lo - padding)) / (range + padding * 2)) * ch;

    // Grid
    ctx.strokeStyle = "#1a1a2e";
    ctx.lineWidth = 0.5;
    for (let i = 0; i < 5; i++) {
      const y = pad.top + (i / 4) * ch;
      ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(w - pad.right, y); ctx.stroke();
    }

    // Candles
    const candleWidth = Math.max(1, cw / display.length * 0.7);
    for (let i = 0; i < display.length; i++) {
      const c = display[i];
      const x = xScale(i) - candleWidth / 2;
      const isUp = c.close >= c.open;
      ctx.fillStyle = isUp ? "#22c55e" : "#ef4444";
      ctx.strokeStyle = isUp ? "#22c55e" : "#ef4444";
      ctx.lineWidth = 0.5;

      // Wick
      ctx.beginPath();
      ctx.moveTo(xScale(i), yScale(c.high));
      ctx.lineTo(xScale(i), yScale(c.low));
      ctx.stroke();

      // Body
      const bodyTop = yScale(Math.max(c.open, c.close));
      const bodyBot = yScale(Math.min(c.open, c.close));
      const bodyH = Math.max(1, bodyBot - bodyTop);
      ctx.fillRect(x, bodyTop, candleWidth, bodyH);
    }

    // Trade markers
    trades.forEach((t) => {
      const idx = display.findIndex((c) => c.timestamp >= t.entry_time);
      if (idx === -1) return;
      const x = xScale(idx);
      const y = yScale(t.entry_price);
      ctx.fillStyle = t.side === "LONG" ? "#22c55e" : "#ef4444";
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = t.pnl > 0 ? "#22c55e" : "#ef4444";
      ctx.font = "7px monospace";
      ctx.fillText(t.pnl > 0 ? "TP" : "SL", x + 4, y - 2);
    });

    // Price axis
    ctx.fillStyle = "#666";
    ctx.font = "8px monospace";
    ctx.textAlign = "right";
    for (let i = 0; i < 5; i++) {
      const v = lo - padding + ((range + padding * 2) * (1 - i / 4));
      const y = pad.top + (i / 4) * ch;
      ctx.fillText(v.toFixed(2), pad.left - 4, y + 3);
    }

    // Latest price
    if (display.length > 0) {
      const last = display[display.length - 1];
      ctx.fillStyle = "#fff";
      ctx.font = "9px monospace";
      ctx.textAlign = "left";
      ctx.fillText(`$${last.close.toFixed(2)}`, pad.left, pad.top - 5);
    }

    // Volume bars
    if (config.whale_simulation) {
      const volMax = Math.max(...display.map((c) => c.volume), 1);
      for (let i = 0; i < display.length; i++) {
        const c = display[i];
        const x = xScale(i) - candleWidth / 2;
        const volH = (c.volume / volMax) * 30;
        ctx.fillStyle = c.close >= c.open ? "rgba(34,197,94,0.15)" : "rgba(239,68,68,0.15)";
        ctx.fillRect(x, h - pad.bottom - volH, candleWidth, volH);
      }
    }
  }, [candles, currentCandle, trades, config.whale_simulation, t]);

  return (
    <canvas ref={canvasRef} className="w-full h-full min-h-[200px]" style={{ display: "block" }} />
  );
}

function ConfigPanel() {
  const { t } = useTranslation("marketSimulator");
  const config = useSimulatorStore((s) => s.config);
  const setConfig = useSimulatorStore((s) => s.setConfig);
  const status = useSimulatorStore((s) => s.status);
  const isActive = status?.active;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
      <div className="space-y-1">
        <label className="text-[8px] uppercase tracking-wider text-[var(--text-tertiary)]">{t("configPanel.symbol")}</label>
        <select value={config.symbol} onChange={(e) => setConfig({ symbol: e.target.value })} disabled={isActive} className="w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded px-2 py-1 text-[10px] font-mono text-[var(--text-primary)] disabled:opacity-40">
          {["BTC", "ETH", "SOL", "HYPE"].map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
      <div className="space-y-1">
        <label className="text-[8px] uppercase tracking-wider text-[var(--text-tertiary)]">{t("configPanel.timeframe")}</label>
        <select value={config.timeframe} onChange={(e) => setConfig({ timeframe: e.target.value })} disabled={isActive} className="w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded px-2 py-1 text-[10px] font-mono disabled:opacity-40">
          {["1m", "5m", "15m", "1h", "4h", "1d"].map((tf) => <option key={tf} value={tf}>{tf}</option>)}
        </select>
      </div>
      <div className="space-y-1">
        <label className="text-[8px] uppercase tracking-wider text-[var(--text-tertiary)]">{t("configPanel.aiMode")}</label>
        <select value={config.ai_mode} onChange={(e) => setConfig({ ai_mode: e.target.value as api.AIDecisionMode })} disabled={isActive} className="w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded px-2 py-1 text-[10px] font-mono disabled:opacity-40">
          <option value="MANUAL">{t("configPanel.aiModeOptions.manual")}</option>
          <option value="AI_ASSISTED">{t("configPanel.aiModeOptions.aiAssisted")}</option>
          <option value="FULL_AI">{t("configPanel.aiModeOptions.fullAi")}</option>
        </select>
      </div>
      <div className="space-y-1">
        <label className="text-[8px] uppercase tracking-wider text-[var(--text-tertiary)]">{t("configPanel.capital")}</label>
        <input type="number" value={config.initial_capital} onChange={(e) => setConfig({ initial_capital: Number(e.target.value) })} disabled={isActive} className="w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded px-2 py-1 text-[10px] font-mono disabled:opacity-40" />
      </div>
      <div className="space-y-1">
        <label className="text-[8px] uppercase tracking-wider text-[var(--text-tertiary)]">{t("configPanel.riskPerTrade")}</label>
        <input type="number" value={config.risk_per_trade * 100} onChange={(e) => setConfig({ risk_per_trade: Number(e.target.value) / 100 })} disabled={isActive} className="w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded px-2 py-1 text-[10px] font-mono disabled:opacity-40" min="0.1" max="10" step="0.1" />
      </div>
      <div className="space-y-1">
        <label className="text-[8px] uppercase tracking-wider text-[var(--text-tertiary)]">{t("configPanel.leverage")}</label>
        <input type="number" value={config.leverage} onChange={(e) => setConfig({ leverage: Number(e.target.value) })} className="w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded px-2 py-1 text-[10px] font-mono" min="1" max="100" />
      </div>
      <div className="space-y-1">
        <label className="text-[8px] uppercase tracking-wider text-[var(--text-tertiary)]">{t("configPanel.slippage")}</label>
        <input type="number" value={config.slippage_bps} onChange={(e) => setConfig({ slippage_bps: Number(e.target.value) })} className="w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded px-2 py-1 text-[10px] font-mono" />
      </div>
      <div className="space-y-1">
        <label className="text-[8px] uppercase tracking-wider text-[var(--text-tertiary)]">{t("configPanel.feeRate")}</label>
        <input type="number" value={config.fee_rate} onChange={(e) => setConfig({ fee_rate: Number(e.target.value) })} className="w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded px-2 py-1 text-[10px] font-mono" step="0.0001" />
      </div>
      <div className="flex items-center gap-2 col-span-2">
        <label className="flex items-center gap-1.5 cursor-pointer">
          <input type="checkbox" checked={config.whale_simulation} onChange={(e) => setConfig({ whale_simulation: e.target.checked })} className="accent-[var(--accent-purple)]" />
          <span className="text-[9px] text-[var(--text-secondary)]">{t("configPanel.whaleSimulation")}</span>
        </label>
        <label className="flex items-center gap-1.5 cursor-pointer">
          <input type="checkbox" checked={config.news_replay} onChange={(e) => setConfig({ news_replay: e.target.checked })} className="accent-[var(--accent-blue)]" />
          <span className="text-[9px] text-[var(--text-secondary)]">{t("configPanel.newsReplay")}</span>
        </label>
        <label className="flex items-center gap-1.5 cursor-pointer">
          <input type="checkbox" checked={config.founder_mode} onChange={(e) => setConfig({ founder_mode: e.target.checked })} className="accent-[var(--accent-purple)]" />
          <span className="text-[9px] text-[var(--text-secondary)]">{t("configPanel.founderMode")}</span>
        </label>
      </div>
    </div>
  );
}

function TradesPanel({ onCloseTrade }: { onCloseTrade: (id: string) => void }) {
  const { t } = useTranslation("marketSimulator");
  const trades = useSimulatorStore((s) => s.trades);
  if (trades.length === 0) return <div className="text-[9px] text-[var(--text-tertiary)] text-center py-4">{t("tradesPanel.empty")}</div>;
  return (
    <div className="space-y-0">
      <div className="grid grid-cols-7 gap-1 text-[8px] uppercase tracking-wider text-[var(--text-tertiary)] pb-1 border-b border-[var(--border-subtle)]">
        <span>{t("tradesPanel.columns.side")}</span><span>{t("tradesPanel.columns.entry")}</span><span>{t("tradesPanel.columns.status")}</span><span>{t("tradesPanel.columns.pnl")}</span><span>{t("tradesPanel.columns.pct")}</span><span>{t("tradesPanel.columns.reason")}</span><span />
      </div>
      {trades.map((trade) => <TradeRow key={trade.id} trade={trade} onClose={onCloseTrade} />)}
    </div>
  );
}

function EquityCurveView() {
  const { t } = useTranslation("marketSimulator");
  const state = useSimulatorStore((s) => s.state);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !state?.equity_curve?.length) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    const w = rect.width;
    const h = rect.height;

    ctx.clearRect(0, 0, w, h);
    const eq = state.equity_curve;
    const vals = eq.map((e) => e.value);
    const min = Math.min(...vals);
    const max = Math.max(...vals);
    const range = max - min || 1;

    ctx.strokeStyle = "#22c55e";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    eq.forEach((e, i) => {
      const x = (i / (eq.length - 1)) * w;
      const y = h - ((e.value - min) / range) * h;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.stroke();

    ctx.fillStyle = "#444";
    ctx.font = "8px monospace";
    ctx.fillText(`$${min.toFixed(0)}`, 2, h - 2);
    ctx.textAlign = "right";
    ctx.fillText(`$${max.toFixed(0)}`, w - 2, 10);
  }, [state?.equity_curve]);

  if (!state?.equity_curve?.length) return <div className="text-[9px] text-[var(--text-tertiary)] text-center py-4">{t("equityCurve.empty")}</div>;
  return <canvas ref={canvasRef} className="w-full h-[80px]" />;
}

function ManualTradingPanel() {
  const { t } = useTranslation("marketSimulator");
  const [side, setSide] = useState<"LONG" | "SHORT">("LONG");
  const [entry, setEntry] = useState("");
  const [sl, setSl] = useState("");
  const [tp, setTp] = useState("");
  const [qty, setQty] = useState("");
  const [lev, setLev] = useState("1");
  const [ts, setTs] = useState("");
  const store = useSimulatorStore();
  const addLog = (msg: string) => console.log(msg);

  const handleSubmit = async () => {
    try {
      await api.manualTrade({
        side, entry_price: Number(entry), stop_loss: Number(sl),
        take_profit: Number(tp), quantity: Number(qty),
        leverage: Number(lev), trailing_stop: ts ? Number(ts) : undefined,
      });
      addLog(`${side} ${store.config.symbol} @ $${entry}`);
    } catch { addLog("Trade failed"); }
  };

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 gap-1">
        <button onClick={() => setSide("LONG")} className={`px-2 py-1 text-[10px] font-semibold rounded border transition-colors ${side === "LONG" ? "bg-[var(--accent-green)]/20 border-[var(--accent-green)] text-[var(--accent-green)]" : "border-[var(--border-subtle)] text-[var(--text-tertiary)]"}`}>{t("manualTrading.buyLong")}</button>
        <button onClick={() => setSide("SHORT")} className={`px-2 py-1 text-[10px] font-semibold rounded border transition-colors ${side === "SHORT" ? "bg-[var(--accent-red)]/20 border-[var(--accent-red)] text-[var(--accent-red)]" : "border-[var(--border-subtle)] text-[var(--text-tertiary)]"}`}>{t("manualTrading.sellShort")}</button>
      </div>
      <div className="grid grid-cols-2 gap-1.5">
        <input placeholder={t("manualTrading.entry")} value={entry} onChange={(e) => setEntry(e.target.value)} className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded px-2 py-1 text-[10px] font-mono" />
        <input placeholder={t("manualTrading.quantity")} value={qty} onChange={(e) => setQty(e.target.value)} className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded px-2 py-1 text-[10px] font-mono" />
        <input placeholder={t("manualTrading.stopLoss")} value={sl} onChange={(e) => setSl(e.target.value)} className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded px-2 py-1 text-[10px] font-mono" />
        <input placeholder={t("manualTrading.takeProfit")} value={tp} onChange={(e) => setTp(e.target.value)} className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded px-2 py-1 text-[10px] font-mono" />
        <input placeholder={t("manualTrading.leverage")} value={lev} onChange={(e) => setLev(e.target.value)} className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded px-2 py-1 text-[10px] font-mono" />
        <input placeholder={t("manualTrading.trailingStop")} value={ts} onChange={(e) => setTs(e.target.value)} className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded px-2 py-1 text-[10px] font-mono" />
      </div>
      <button onClick={handleSubmit} className="w-full px-2 py-1.5 text-[10px] font-semibold bg-[var(--accent-cyan)]/20 text-[var(--accent-cyan)] border border-[var(--accent-cyan)]/30 rounded hover:bg-[var(--accent-cyan)]/30 transition-colors">{t("manualTrading.execute", { side })}</button>
    </div>
  );
}

function AIDecisionPanel() {
  const { t } = useTranslation("marketSimulator");
  const decisions = useSimulatorStore((s) => s.decisions);
  const latest = decisions[decisions.length - 1];
  if (!latest) return <div className="text-[9px] text-[var(--text-tertiary)] text-center py-4">{t("aiDecisions.waiting")}</div>;
  return (
    <div className="space-y-1.5">
      <div className="flex items-center gap-2">
        <span className={`px-1.5 py-0.5 text-[9px] font-semibold rounded ${latest.decision === "BUY" ? "bg-[var(--accent-green)]/20 text-[var(--accent-green)]" : latest.decision === "SELL" ? "bg-[var(--accent-red)]/20 text-[var(--accent-red)]" : "bg-[var(--text-tertiary)]/20 text-[var(--text-tertiary)]"}`}>{latest.decision}</span>
        <span className="text-[9px] text-[var(--text-secondary)]">{latest.side}</span>
        <span className="text-[9px] text-[var(--text-secondary)]">${latest.price.toFixed(2)}</span>
      </div>
      <div className="grid grid-cols-3 gap-1">
        <Metric label={t("aiDecisions.confidence")} value={`${latest.confidence.toFixed(0)}%`} positive={latest.confidence > 60} />
        <Metric label={t("aiDecisions.evidence")} value={`${latest.evidence_strength.toFixed(0)}%`} positive={latest.evidence_strength > 60} />
        <Metric label={t("aiDecisions.risk")} value={`${latest.risk_score.toFixed(0)}%`} negative={latest.risk_score > 60} />
      </div>
      {latest.conflicts.length > 0 && (
        <div className="text-[8px] text-[var(--accent-yellow)]">{latest.conflicts.join("; ")}</div>
      )}
      {latest.agent_reports.length > 0 && (
        <div className="space-y-0.5 max-h-[80px] overflow-y-auto">
          {latest.agent_reports.slice(0, 6).map((r, i) => (
            <div key={i} className="flex items-center justify-between text-[8px] font-mono">
              <span className="text-[var(--text-secondary)]">{String(r.agent_name || r.name || `Agent ${i}`)}</span>
              <span className={String(r.direction || "").includes("BULL") ? "text-[var(--accent-green)]" : String(r.direction || "").includes("BEAR") ? "text-[var(--accent-red)]" : "text-[var(--text-tertiary)]"}>
                {String(r.direction || "?")} {(r.confidence ? `${(Number(r.confidence) * 100).toFixed(0)}%` : "")}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function AIExplainPanel() {
  const { t } = useTranslation("marketSimulator");
  const decisions = useSimulatorStore((s) => s.decisions);
  const latest = decisions[decisions.length - 1];
  if (!latest?.explanation) return <div className="text-[9px] text-[var(--text-tertiary)] text-center py-4">{t("aiExplain.empty")}</div>;
  const exp = latest.explanation;
  return (
    <div className="space-y-1.5 text-[9px]">
      <div className="text-[var(--text-primary)] font-semibold">{String(exp.summary || "N/A")}</div>
      {(exp.reasons as string[] || []).map((r: string, i: number) => (
        <div key={i} className="text-[var(--text-secondary)] flex gap-1"><span className="text-[var(--text-tertiary)]">•</span>{r}</div>
      ))}
      {(exp.warnings as string[] || []).length > 0 && (
        <div className="text-[var(--accent-yellow)] mt-1">
          {(exp.warnings as string[]).map((w: string, i: number) => <div key={i} className="flex gap-1"><span>⚠</span>{w}</div>)}
        </div>
      )}
      <div className="grid grid-cols-3 gap-1 mt-1">
        <Metric label={t("aiExplain.whyNow")} value={latest.confidence > 60 ? t("aiExplain.confidenceHigh") : t("aiExplain.lowConviction")} positive={latest.confidence > 60} />
        <Metric label={t("aiExplain.evidence")} value={`${latest.evidence_strength.toFixed(0)}%`} positive={latest.evidence_strength > 60} />
        <Metric label={t("aiExplain.conflicts")} value={String(latest.conflicts.length || "0")} negative={latest.conflicts.length > 0} />
      </div>
    </div>
  );
}

function MissionTimelinePanel() {
  const { t } = useTranslation("marketSimulator");
  const timeline = useSimulatorStore((s) => s.timeline);
  const reversed = [...timeline].reverse().slice(0, 50);
  if (reversed.length === 0) return <div className="text-[9px] text-[var(--text-tertiary)] text-center py-4">{t("missionTimeline.empty")}</div>;
  return (
    <div className="space-y-0.5 overflow-y-auto max-h-[200px]">
      {reversed.map((e) => (
        <div key={e.id} className="flex items-start gap-1.5 text-[8px] font-mono">
          <span className={`inline-block w-1.5 h-1.5 rounded-full mt-0.5 flex-shrink-0 ${e.severity === "trade" ? "bg-[var(--accent-green)]" : e.severity === "decision" ? "bg-[var(--accent-cyan)]" : e.severity === "error" ? "bg-[var(--accent-red)]" : "bg-[var(--text-tertiary)]"}`} />
          <span className="text-[var(--text-tertiary)] flex-shrink-0">{(new Date(e.timestamp)).toLocaleTimeString()}</span>
          <span className="text-[var(--text-secondary)]">{e.title}</span>
        </div>
      ))}
    </div>
  );
}

function MarketInfoPanel() {
  const { t } = useTranslation("marketSimulator");
  const state = useSimulatorStore((s) => s.state);
  const status = useSimulatorStore((s) => s.status);
  if (!state && !status) return <div className="text-[9px] text-[var(--text-tertiary)]">No data</div>;
  return (
    <div className="grid grid-cols-3 gap-1">
      <Metric label={t("marketInfo.regime")} value={state?.regime || status?.regime || "N/A"} neutral />
      <Metric label={t("marketInfo.portfolio")} value={`$${(state?.portfolio_value || 0).toFixed(0)}`} positive={(state?.portfolio_value || 0) > (state?.config.initial_capital || 0)} />
      <Metric label={t("marketInfo.drawdown")} value={state?.total_pnl && state.total_pnl < 0 ? t("marketInfo.active") : t("marketInfo.none")} negative={state?.total_pnl ? state.total_pnl < 0 : false} />
      <Metric label={t("marketInfo.trades")} value={String(state?.trades?.length || status?.trades || 0)} />
      <Metric label={t("marketInfo.winRate")} value={(() => { const s = state; if (!s || s.win_count + s.loss_count === 0) return "-"; return `${(s.win_count / (s.win_count + s.loss_count) * 100).toFixed(0)}%`; })()} positive />
      <Metric label={t("marketInfo.open")} value={String(state?.open_positions || 0)} />
    </div>
  );
}

/* ── Modals ──────────────────────────────────────────────────────────────── */

function ReportModal({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation("marketSimulator");
  const report = useSimulatorStore((s) => s.report);
  if (!report) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded w-[700px] max-h-[80vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)]">
          <span className="text-xs font-semibold uppercase tracking-widest">{t("reportModal.title")}</span>
          <button onClick={onClose} className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)]">&times;</button>
        </div>
        <div className="p-4 space-y-4">
          <div className="grid grid-cols-4 gap-2">
            <Metric label={t("reportModal.totalPnl")} value={`$${report.total_pnl.toFixed(2)}`} positive={report.total_pnl >= 0} />
            <Metric label={t("reportModal.return")} value={`${report.return_pct.toFixed(2)}%`} positive={report.return_pct >= 0} />
            <Metric label={t("reportModal.winRate")} value={`${report.win_rate.toFixed(1)}%`} positive={report.win_rate >= 50} />
            <Metric label={t("reportModal.sharpe")} value={report.sharpe_ratio.toFixed(2)} positive={report.sharpe_ratio >= 1} />
            <Metric label={t("reportModal.profitFactor")} value={report.profit_factor.toFixed(2)} positive={report.profit_factor >= 1.5} />
            <Metric label={t("reportModal.maxDd")} value={`${report.max_drawdown_pct.toFixed(1)}%`} negative={report.max_drawdown_pct > 10} />
            <Metric label={t("reportModal.trades")} value={String(report.total_trades)} />
            <Metric label={t("reportModal.avgHold")} value={`${(report.avg_holding_time / 3600).toFixed(1)}h`} />
          </div>

          <div>
            <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)] mb-1">{t("reportModal.trainingScores")}</div>
            <div className="grid grid-cols-4 gap-1">
              <Metric label={t("reportModal.patience")} value={`${report.training_score.patience.toFixed(0)}`} positive={report.training_score.patience >= 60} />
              <Metric label={t("reportModal.risk")} value={`${report.training_score.risk.toFixed(0)}`} positive={report.training_score.risk >= 60} />
              <Metric label={t("reportModal.timing")} value={`${report.training_score.timing.toFixed(0)}`} positive={report.training_score.timing >= 60} />
              <Metric label={t("reportModal.entry")} value={`${report.training_score.entry_quality.toFixed(0)}`} positive={report.training_score.entry_quality >= 60} />
              <Metric label={t("reportModal.exit")} value={`${report.training_score.exit_quality.toFixed(0)}`} positive={report.training_score.exit_quality >= 60} />
              <Metric label={t("reportModal.psychology")} value={`${report.training_score.psychology.toFixed(0)}`} positive={report.training_score.psychology >= 60} />
              <Metric label={t("reportModal.discipline")} value={`${report.training_score.discipline.toFixed(0)}`} positive={report.training_score.discipline >= 60} />
              <Metric label={t("reportModal.mistakes")} value={String(report.training_score.mistakes)} negative={report.training_score.mistakes > 0} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)] mb-1">{t("reportModal.mistakes")}</div>
              <ul className="text-[9px] text-[var(--accent-red)] space-y-0.5 list-disc list-inside">
                {report.mistakes.map((m, i) => <li key={i}>{m}</li>)}
              </ul>
            </div>
            <div>
              <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)] mb-1">{t("reportModal.lessons")}</div>
              <ul className="text-[9px] text-[var(--accent-green)] space-y-0.5 list-disc list-inside">
                {report.lessons.map((l, i) => <li key={i}>{l}</li>)}
              </ul>
            </div>
          </div>

          <div>
            <div className="text-[9px] uppercase tracking-wider text-[var(--text-secondary)] mb-1">{t("reportModal.aiRecommendations")}</div>
            <ul className="text-[9px] text-[var(--accent-cyan)] space-y-0.5 list-disc list-inside">
              {report.ai_recommendations.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

function ScenariosModal({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation("marketSimulator");
  const [scenarios, setScenarios] = useState<Record<string, { name: string; description: string }>>({});
  const store = useSimulatorStore();

  useEffect(() => {
    api.listScenarios().then((r) => setScenarios(r.scenarios)).catch(() => {});
  }, []);

  const handleSelect = (key: string) => {
    store.setConfig({ scenario: key as api.ScenarioType });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded w-[500px] max-h-[70vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)]">
          <span className="text-xs font-semibold uppercase tracking-widest">{t("scenariosModal.title")}</span>
          <button onClick={onClose} className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)]">&times;</button>
        </div>
        <div className="p-3 grid grid-cols-1 gap-1.5">
          {Object.entries(scenarios).map(([key, s]) => (
            <button key={key} onClick={() => handleSelect(key)} className="text-left px-3 py-2 border border-[var(--border-subtle)] rounded hover:bg-[var(--bg-surface)] transition-colors">
              <div className="text-[10px] font-semibold text-[var(--text-primary)]">{s.name}</div>
              <div className="text-[8px] text-[var(--text-tertiary)]">{s.description}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function SessionsModal({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation("marketSimulator");
  const [sessions, setSessions] = useState<api.SessionMeta[]>([]);
  const store = useSimulatorStore();

  const load = useCallback(() => {
    api.listSessions().then((r) => setSessions(r.sessions)).catch(() => {});
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleLoad = async (id: string) => {
    try {
      const state = await api.getSession(id);
      store.setState(state);
      store.setConfig(state.config);
      onClose();
    } catch { /* ignore */ }
  };

  const handleDelete = async (id: string) => {
    await api.deleteSession(id);
    load();
  };

  const handleSave = async () => {
    if (!store.state?.session_id) return;
    await api.saveSession(store.state.session_id);
    load();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div className="bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded w-[500px] max-h-[70vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)]">
          <span className="text-xs font-semibold uppercase tracking-widest">{t("sessionsModal.title")}</span>
          <div className="flex items-center gap-2">
            {store.state && <button onClick={handleSave} className="px-2 py-0.5 text-[9px] border border-[var(--border-subtle)] rounded hover:bg-[var(--bg-surface)]">{t("sessionsModal.saveCurrent")}</button>}
            <button onClick={onClose} className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)]">&times;</button>
          </div>
        </div>
        <div className="p-3 space-y-1">
          {sessions.length === 0 && <div className="text-[9px] text-[var(--text-tertiary)] text-center py-4">{t("sessionsModal.empty")}</div>}
          {sessions.map((s) => (
            <div key={s.id} className="flex items-center justify-between px-3 py-2 border border-[var(--border-subtle)] rounded text-[9px]">
              <div>
                <span className="text-[var(--text-primary)] font-semibold">{s.name}</span>
                <span className="text-[var(--text-tertiary)] ml-2">{s.config.symbol} {s.config.timeframe}</span>
                <span className="text-[var(--text-tertiary)] ml-2">{s.total_trades} {t("sessionsModal.trades")} | ${s.total_pnl.toFixed(2)}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <button onClick={() => handleLoad(s.id)} className="text-[var(--accent-cyan)] hover:underline">{t("sessionsModal.load")}</button>
                <button onClick={() => handleDelete(s.id)} className="text-[var(--accent-red)] hover:underline">{t("sessionsModal.delete")}</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function FounderModePanel() {
  const { t } = useTranslation("marketSimulator");
  const state = useSimulatorStore((s) => s.state);
  if (!state?.founder_metrics) return null;
  const m = state.founder_metrics;
  return (
    <div className="fixed bottom-0 right-0 z-40 m-2 p-2 bg-[var(--bg-elevated)] border border-[var(--accent-purple)]/30 rounded shadow-lg">
      <div className="text-[7px] uppercase tracking-widest text-[var(--accent-purple)] mb-1">{t("founderMode.title")}</div>
      <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-[8px] font-mono">
        <span className="text-[var(--text-tertiary)]">{t("founderMode.aiLatency")}</span><span className="text-[var(--text-primary)]">{m.ai_latency_ms?.toFixed(1) || "N/A"}ms</span>
        <span className="text-[var(--text-tertiary)]">{t("founderMode.decisionLatency")}</span><span className="text-[var(--text-primary)]">{m.decision_latency_ms?.toFixed(1) || "N/A"}ms</span>
        <span className="text-[var(--text-tertiary)]">{t("founderMode.evidenceLatency")}</span><span className="text-[var(--text-primary)]">{m.evidence_latency_ms?.toFixed(1) || "N/A"}ms</span>
        <span className="text-[var(--text-tertiary)]">{t("founderMode.candlesPerSec")}</span><span className="text-[var(--text-primary)]">{(state.total_candles / (state.elapsed_seconds || 1)).toFixed(1)}</span>
        <span className="text-[var(--text-tertiary)]">{t("founderMode.memory")}</span><span className="text-[var(--text-primary)]">{state.trades.length} {t("founderMode.trades")} / {state.decisions.length} {t("founderMode.decisions")}</span>
      </div>
    </div>
  );
}

function WhaleOverlay() {
  const { t } = useTranslation("marketSimulator");
  const store = useSimulatorStore((s) => s);
  if (!store.config.whale_simulation) return null;
  return (
    <div className="fixed bottom-0 left-0 z-40 m-2 p-2 bg-[var(--bg-elevated)] border border-[var(--accent-purple)]/20 rounded shadow-lg">
      <div className="text-[7px] uppercase tracking-widest text-[var(--accent-purple)] mb-1">{t("whaleOverlay.title")}</div>
      <div className="text-[8px] text-[var(--text-tertiary)] font-mono">{t("whaleOverlay.text")}</div>
    </div>
  );
}

function NewsOverlay() {
  const { t } = useTranslation("marketSimulator");
  const store = useSimulatorStore((s) => s);
  if (!store.config.news_replay) return null;
  return (
    <div className="fixed top-16 right-0 z-40 m-2 p-2 bg-[var(--bg-elevated)] border border-[var(--accent-blue)]/20 rounded shadow-lg max-w-[250px]">
      <div className="text-[7px] uppercase tracking-widest text-[var(--accent-blue)] mb-1">{t("newsOverlay.title")}</div>
      <div className="text-[8px] text-[var(--text-tertiary)] font-mono">{t("newsOverlay.text")}</div>
    </div>
  );
}

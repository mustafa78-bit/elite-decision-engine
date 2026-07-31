import { apiFetch } from "./client";

export type SimStatus = "IDLE" | "RUNNING" | "PAUSED" | "COMPLETED" | "STOPPED";
export type SimSpeed = "1x" | "2x" | "5x" | "10x" | "100x" | "unlimited";
export type AIDecisionMode = "MANUAL" | "AI_ASSISTED" | "FULL_AI";
export type ScenarioType =
  | "FLASH_CRASH" | "BULL_RUN" | "CAPITULATION" | "RANGE"
  | "WHALE_ACCUMULATION" | "WHALE_DISTRIBUTION" | "ETF_NEWS"
  | "EXCHANGE_LISTING" | "BLACK_SWAN" | "CUSTOM";
export type MarketRegime = "BULL" | "BEAR" | "SIDEWAYS" | "VOLATILE" | "RISK_ON" | "RISK_OFF";

export interface SimulatorConfig {
  symbol: string;
  timeframe: string;
  start_date?: string;
  end_date?: string;
  initial_capital: number;
  ai_mode: AIDecisionMode;
  speed: SimSpeed;
  scenario?: ScenarioType;
  slippage_bps: number;
  fee_rate: number;
  leverage: number;
  risk_per_trade: number;
  founder_mode: boolean;
  whale_simulation: boolean;
  news_replay: boolean;
}

export interface SimulatedCandle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface SimulatedDecision {
  id: string;
  symbol: string;
  side: string;
  timestamp: number;
  price: number;
  decision: string;
  confidence: number;
  evidence_strength: number;
  risk_score: number;
  council_report?: Record<string, unknown>;
  evidence_report?: Record<string, unknown>;
  explanation?: Record<string, unknown>;
  agent_reports: Record<string, unknown>[];
  conflicts: string[];
}

export interface SimulatedTrade {
  id: string;
  symbol: string;
  side: string;
  entry_price: number;
  entry_time: number;
  quantity: number;
  leverage: number;
  stop_loss: number;
  take_profit: number;
  trailing_stop?: number;
  status: string;
  exit_price?: number;
  exit_time?: number;
  pnl: number;
  pnl_percent: number;
  fees: number;
  slippage: number;
  close_reason?: string;
  decision_id?: string;
  elite_score?: number;
  entry_decision?: Record<string, unknown>;
  exit_decision?: Record<string, unknown>;
}

export interface TimelineEvent {
  id: string;
  timestamp: number;
  event_type: string;
  symbol: string;
  title: string;
  description: string;
  severity: string;
  data?: Record<string, unknown>;
}

export interface SimulatorState {
  session_id: string;
  status: SimStatus;
  config: SimulatorConfig;
  current_candle_index: number;
  total_candles: number;
  current_timestamp?: number;
  current_price?: number;
  elapsed_seconds: number;
  regime: MarketRegime;
  portfolio_value: number;
  cash: number;
  open_positions: number;
  total_pnl: number;
  win_count: number;
  loss_count: number;
  trades: SimulatedTrade[];
  decisions: SimulatedDecision[];
  timeline: TimelineEvent[];
  equity_curve: { timestamp: number; value: number; price: number }[];
  founder_metrics?: Record<string, number>;
}

export interface MissionReport {
  session_id: string;
  config: SimulatorConfig;
  duration_seconds: number;
  total_candles: number;
  total_decisions: number;
  total_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  total_pnl: number;
  total_fees: number;
  total_slippage: number;
  max_drawdown: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
  profit_factor: number;
  avg_win: number;
  avg_loss: number;
  largest_win: number;
  largest_loss: number;
  avg_holding_time: number;
  final_portfolio_value: number;
  return_pct: number;
  regime_changes: { timestamp: number; regime: string; title: string }[];
  elite_scores: { overall: number; confidence: number; evidence_strength: number; risk: number; execution: number; reward: number }[];
  training_score: {
    patience: number; risk: number; timing: number; entry_quality: number;
    exit_quality: number; psychology: number; discipline: number;
    missed_trades: number; mistakes: number;
  };
  trades: SimulatedTrade[];
  decisions: SimulatedDecision[];
  timeline: TimelineEvent[];
  equity_curve: { timestamp: number; value: number; price: number }[];
  mistakes: string[];
  lessons: string[];
  ai_recommendations: string[];
}

export interface SimulatorStatus {
  active: boolean;
  running: boolean;
  status: string;
  session_id?: string;
  progress: number;
  current_candle: number;
  total_candles: number;
  current_price?: number;
  regime: string;
  trades: number;
  open_positions: number;
  total_pnl: number;
  portfolio_value: number;
  founder_mode: boolean;
  founder_metrics?: Record<string, number>;
}

export interface SessionMeta {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  config: SimulatorConfig;
  status: string;
  total_trades: number;
  total_pnl: number;
  win_rate: number;
}

export interface ScenarioInfo {
  name: string;
  description: string;
}

export function getSimulatorStatus(): Promise<SimulatorStatus> {
  return apiFetch<SimulatorStatus>("/simulator/status");
}

export function getSimulatorState(): Promise<{ status: string; state: SimulatorState | null }> {
  return apiFetch("/simulator/state");
}

export function startSimulation(config: SimulatorConfig, name = ""): Promise<{ session_id: string; state: SimulatorState }> {
  return apiFetch("/simulator/start", {
    method: "POST",
    body: JSON.stringify({ config, name }),
  });
}

export function pauseSimulation(): Promise<{ status: string }> {
  return apiFetch("/simulator/pause", { method: "POST" });
}

export function resumeSimulation(): Promise<{ status: string }> {
  return apiFetch("/simulator/resume", { method: "POST" });
}

export function stopSimulation(): Promise<{ status: string; state: SimulatorState }> {
  return apiFetch("/simulator/stop", { method: "POST" });
}

export function resetSimulation(): Promise<{ status: string }> {
  return apiFetch("/simulator/reset", { method: "POST" });
}

export function stepSimulation(): Promise<{ candle: SimulatedCandle; state: SimulatorState }> {
  return apiFetch("/simulator/step", { method: "POST" });
}

export function setSpeed(speed: SimSpeed): Promise<{ speed: string }> {
  return apiFetch(`/simulator/speed?speed=${speed}`, { method: "POST" });
}

export function seekTo(timestamp: number): Promise<{ state: SimulatorState }> {
  return apiFetch(`/simulator/seek?timestamp=${timestamp}`, { method: "POST" });
}

export function manualTrade(params: {
  side: string; entry_price: number; stop_loss: number; take_profit: number;
  quantity: number; leverage?: number; trailing_stop?: number;
}): Promise<{ trade: SimulatedTrade }> {
  const qs = Object.entries(params)
    .filter(([_, v]) => v !== undefined)
    .map(([k, v]) => `${k}=${v}`)
    .join("&");
  return apiFetch(`/simulator/trade?${qs}`, { method: "POST" });
}

export function closeTrade(tradeId: string, exitPrice?: number): Promise<{ closed: boolean }> {
  const qs = exitPrice ? `?exit_price=${exitPrice}` : "";
  return apiFetch(`/simulator/trade/${tradeId}/close${qs}`, { method: "POST" });
}

export function closeAllTrades(exitPrice?: number): Promise<{ closed_count: number }> {
  const qs = exitPrice ? `?exit_price=${exitPrice}` : "";
  return apiFetch(`/simulator/trades/close-all${qs}`, { method: "POST" });
}

export function getReport(): Promise<MissionReport> {
  return apiFetch("/simulator/report");
}

export function exportReportJson(): Promise<string> {
  return apiFetch("/simulator/report/json");
}

export function getReportPdfUrl(): string {
  return `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/simulator/report/pdf`;
}

export function listSessions(): Promise<{ sessions: SessionMeta[] }> {
  return apiFetch("/simulator/sessions");
}

export function getSession(sessionId: string): Promise<SimulatorState> {
  return apiFetch(`/simulator/sessions/${sessionId}`);
}

export function deleteSession(sessionId: string): Promise<{ deleted: boolean }> {
  return apiFetch(`/simulator/sessions/${sessionId}`, { method: "DELETE" });
}

export function saveSession(sessionId: string, name = ""): Promise<{ saved: boolean }> {
  return apiFetch(`/simulator/sessions/${sessionId}/save?name=${encodeURIComponent(name)}`, { method: "POST" });
}

export function compareSessions(idA: string, idB: string): Promise<Record<string, unknown>> {
  return apiFetch(`/simulator/sessions/compare/${idA}/${idB}`);
}

export function listScenarios(): Promise<{ scenarios: Record<string, ScenarioInfo> }> {
  return apiFetch("/simulator/scenarios");
}

export function generateScenario(
  scenario_type: ScenarioType, symbol = "BTC", timeframe = "1h",
  num_candles = 200, start_price?: number
): Promise<{ scenario: string; candles: SimulatedCandle[]; count: number }> {
  const qs = `scenario_type=${scenario_type}&symbol=${symbol}&timeframe=${timeframe}&num_candles=${num_candles}${start_price ? `&start_price=${start_price}` : ""}`;
  return apiFetch(`/simulator/scenarios/generate?${qs}`, { method: "POST" });
}

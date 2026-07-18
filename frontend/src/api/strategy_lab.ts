import { apiFetch } from "./client";

export interface Condition {
  type: string; // 'mtf', 'indicator', 'news', 'whale', 'portfolio'
  param: string;
  operator: string;
  value: any;
}

export interface Strategy {
  id?: number;
  name: string;
  description?: string;
  rules: Condition[];
  parameters: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface BacktestSummary {
  total_signals_scanned: number;
  signals_filtered: number;
  capital_utilized: number;
}

export interface BacktestPerformance {
  total_pnl: number;
  roi_pct: number;
  win_rate_pct: number;
  win_rate_long_pct: number;
  win_rate_short_pct: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
  max_drawdown: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  calmar_ratio: number;
  expectancy: number;
}

export interface SimulatedTrade {
  id: number;
  symbol: string;
  side: string;
  entry: number;
  exit: number;
  quantity: number;
  pnl: number;
  status: string;
  close_reason: string;
  created_at: string | null;
  closed_at: string | null;
}

export interface LabBacktestResult {
  summary: BacktestSummary;
  performance: BacktestPerformance;
  trades: SimulatedTrade[];
  equity_curve: { timestamp: string | null; equity: number }[];
  monthly_pnl: Record<string, number>;
}

export interface Trial {
  parameters: Record<string, any>;
  sharpe_ratio: number;
  total_pnl: number;
  win_rate_pct: number;
  max_drawdown_pct: number;
}

export interface OptimizeResult {
  best_parameters: Record<string, any>;
  best_sharpe: number;
  trials: Trial[];
}

export interface WalkForwardWindow {
  train_start: string;
  train_end: string;
  test_start: string;
  test_end: string;
  train_sharpe: number;
  train_pnl: number;
  test_sharpe: number;
  test_pnl: number;
}

export interface WalkForwardResult {
  windows: WalkForwardWindow[];
  avg_train_sharpe: number;
  avg_test_sharpe: number;
  stability: number;
  combined_test_pnl: number;
}

export interface MonteCarloResult {
  simulations: number[][];
  metrics: {
    probability_of_ruin_pct: number;
    avg_drawdown_pct: number;
    percentile_95_drawdown_pct: number;
    median_terminal_equity: number;
    min_terminal_equity: number;
    max_terminal_equity: number;
  };
}

export interface SensitivityItem {
  perturbation_pct: string;
  parameter_value: number;
  sharpe_ratio: number;
  total_pnl: number;
  win_rate_pct: number;
  max_drawdown_pct: number;
}

export interface SensitivityResult {
  parameter: string;
  base_value: number;
  sensitivity_matrix: SensitivityItem[];
}

export interface AIAnalysisResult {
  strengths: string[];
  weaknesses: string[];
  improvements: string[];
  missing_filters: string[];
}

// API Methods
export function fetchTemplates(): Promise<Strategy[]> {
  return apiFetch<Strategy[]>("/strategy-lab/templates");
}

export function fetchSavedStrategies(): Promise<Strategy[]> {
  return apiFetch<Strategy[]>("/strategy-lab/saved");
}

export function saveStrategy(strategy: Strategy): Promise<{ status: string; id: number; message: string }> {
  return apiFetch<{ status: string; id: number; message: string }>("/strategy-lab/save", {
    method: "POST",
    body: JSON.stringify(strategy),
  });
}

export function deleteStrategy(id: number): Promise<{ status: string; message: string }> {
  return apiFetch<{ status: string; message: string }>(`/strategy-lab/delete/${id}`, {
    method: "DELETE",
  });
}

export function runLabBacktest(strategy: Strategy): Promise<LabBacktestResult> {
  return apiFetch<LabBacktestResult>("/strategy-lab/backtest", {
    method: "POST",
    body: JSON.stringify(strategy),
  });
}

export function runLabOptimize(rules: Condition[], paramRanges?: Record<string, any[]>): Promise<OptimizeResult> {
  return apiFetch<OptimizeResult>("/strategy-lab/optimize", {
    method: "POST",
    body: JSON.stringify({ rules, param_ranges: paramRanges }),
  });
}

export function runLabWalkForward(rules: Condition[], config?: { window_size_days?: number; test_size_days?: number; step_days?: number }): Promise<WalkForwardResult> {
  return apiFetch<WalkForwardResult>("/strategy-lab/walk-forward", {
    method: "POST",
    body: JSON.stringify({ rules, ...config }),
  });
}

export function runLabMonteCarlo(rules: Condition[], config?: { initial_capital?: number; num_simulations?: number; num_trades?: number }): Promise<MonteCarloResult> {
  return apiFetch<MonteCarloResult>("/strategy-lab/monte-carlo", {
    method: "POST",
    body: JSON.stringify({ rules, ...config }),
  });
}

export function runLabSensitivity(rules: Condition[], parameterToPerturb: string, baseValue: number): Promise<SensitivityResult> {
  return apiFetch<SensitivityResult>("/strategy-lab/sensitivity", {
    method: "POST",
    body: JSON.stringify({ rules, parameter_to_perturb: parameterToPerturb, base_value: baseValue }),
  });
}

export function runLabAIGenerate(style: string, riskLevel = "Medium"): Promise<Strategy> {
  return apiFetch<Strategy>("/strategy-lab/ai-generate", {
    method: "POST",
    body: JSON.stringify({ style, risk_level: riskLevel }),
  });
}

export function runLabAIAnalyze(rules: Condition[], metrics: Record<string, any>): Promise<AIAnalysisResult> {
  return apiFetch<AIAnalysisResult>("/strategy-lab/ai-analyze", {
    method: "POST",
    body: JSON.stringify({ rules, metrics }),
  });
}

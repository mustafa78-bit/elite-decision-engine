import { apiFetch } from "./client";

export interface PerformanceStats {
  sharpe_ratio: number;
  sortino_ratio: number;
  profit_factor: number;
  expectancy: number;
  recovery_factor: number;
  calmar_ratio: number;
  average_r_multiple: number;
  average_holding_hours: number;
  consecutive_wins: number;
  consecutive_losses: number;
  best_trade: number;
  worst_trade: number;
}

export function fetchPerformance(): Promise<PerformanceStats> {
  return apiFetch<PerformanceStats>("/performance");
}

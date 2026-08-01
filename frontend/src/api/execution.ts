import { apiFetch } from "./client";

export interface ExecutionData {
  signals: {
    total: number;
    approved: number;
    rejected: number;
    pending: number;
    execution_rate: number;
  };
  trades: {
    total: number;
    open: number;
    closed: number;
    tp_hit: number;
    sl_hit: number;
  };
  errors: string[];
}

export function fetchExecutionStatus(): Promise<ExecutionData> {
  return apiFetch<ExecutionData>("/execution/status");
}

import { apiFetch } from "./client";

export interface AgentReportData {
  agent_name: string;
  symbol: string;
  direction: string;
  confidence: number;
  score: number;
  reasoning: string[];
  data_points: Record<string, unknown>;
  latency_ms: number;
  timestamp: string;
}

export interface CouncilReportData {
  symbol: string;
  timestamp: string;
  consensus_direction: string;
  consensus_score: number;
  agreement_level: string;
  agent_reports: AgentReportData[];
  coordinator_report: Record<string, unknown> | null;
  agent_count: number;
  sources_agreeing: number;
  sources_disagreeing: number;
}

export interface CouncilStatusData {
  agent_count: number;
  agents: string[];
  weights: Record<string, number>;
  stats: Record<string, unknown>;
}

export async function getCouncilStatus(): Promise<CouncilStatusData> {
  return apiFetch<CouncilStatusData>("/council");
}

export async function evaluateSignal(
  signalId: number,
): Promise<{ signal_id: number; symbol: string; council_report: CouncilReportData }> {
  return apiFetch(`/council/evaluate/${signalId}`);
}

export async function evaluateSymbol(
  symbol: string,
  side: string = "LONG",
  timeframe: string = "1h",
): Promise<{ symbol: string; side: string; council_report: CouncilReportData }> {
  return apiFetch(`/council/evaluate?symbol=${encodeURIComponent(symbol)}&side=${encodeURIComponent(side)}&timeframe=${encodeURIComponent(timeframe)}`, {
    method: "POST",
  });
}

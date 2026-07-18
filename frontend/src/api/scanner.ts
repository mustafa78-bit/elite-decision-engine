import { apiFetch } from "./client";

export interface ScannerOpportunity {
  rank: number;
  symbol: string;
  side: string;
  strategy: string;
  score: number;
  probability: number;
  risk_score: number;
  confidence: number;
  price: number | null;
  signals: string[];
}

export interface ScannerDashboard {
  symbols_scanned: number;
  opportunities_found: number;
  top_opportunities: ScannerOpportunity[];
  top_signals: string[];
  market_summary: Record<string, unknown>;
  intelligence_summary: Record<string, unknown>;
  timestamp: string;
}

export function fetchScannerDashboard(n = 5): Promise<ScannerDashboard> {
  return apiFetch<ScannerDashboard>(`/scanner/dashboard?n=${n}`);
}

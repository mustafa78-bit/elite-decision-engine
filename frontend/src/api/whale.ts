import { apiFetch } from "./client";

export interface WhaleActivity {
  type: string;
  symbol: string;
  severity: string;
  description: string;
  confidence: number;
  timestamp: string;
}

export function fetchWhaleActivity(): Promise<WhaleActivity[]> {
  return apiFetch<WhaleActivity[]>("/whale/activity");
}

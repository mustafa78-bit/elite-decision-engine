import { apiFetch } from "./client";

export interface JournalEntryRow {
  id: number;
  symbol: string;
  side: string;
  entry_price: number;
  exit_price: number | null;
  score: number;
  confidence: number;
  entry_reason: string;
  exit_reason: string | null;
  notes: string | null;
  result: string;
  pnl: number;
  signal_id: number | null;
  trade_id: number | null;
  created_at: string | null;
}

export interface JournalCreatePayload {
  symbol: string;
  side: string;
  entry_price: number;
  exit_price?: number;
  score?: number;
  confidence?: number;
  entry_reason?: string;
  exit_reason?: string;
  notes?: string;
  result?: string;
  pnl?: number;
  signal_id?: number;
  trade_id?: number;
}

export function fetchJournal(limit = 100): Promise<JournalEntryRow[]> {
  return apiFetch<JournalEntryRow[]>(`/journal?limit=${limit}`);
}

export function createJournalEntry(body: JournalCreatePayload): Promise<{ id: number } | { error: string }> {
  return apiFetch<{ id: number } | { error: string }>("/journal", { method: "POST", body: JSON.stringify(body) });
}

export function deleteJournalEntry(id: number): Promise<{ status: string } | { error: string }> {
  return apiFetch<{ status: string } | { error: string }>(`/journal/${id}`, { method: "DELETE" });
}

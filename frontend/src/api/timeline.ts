import { apiFetch } from "./client";
import type { TimelineResponseDTO } from "../types/api/timeline";

export function fetchSignalTimeline(signalId: number): Promise<TimelineResponseDTO> {
  return apiFetch(`/timeline/signal/${signalId}`);
}

export function fetchTradeTimeline(tradeId: number): Promise<TimelineResponseDTO> {
  return apiFetch(`/timeline/trade/${tradeId}`);
}

export function fetchGlobalTimeline(params?: {
  type?: string;
  offset?: number;
  limit?: number;
}): Promise<TimelineResponseDTO> {
  const search = new URLSearchParams();
  if (params?.type) search.set("type", params.type);
  if (params?.offset) search.set("offset", String(params.offset));
  if (params?.limit) search.set("limit", String(params.limit));
  const qs = search.toString();
  return apiFetch(`/timeline${qs ? `?${qs}` : ""}`);
}

import { apiFetch } from "./client";
import type { WatchlistDTO, WatchlistUpdateDTO } from "../types/api/watchlist";

export function fetchWatchlists(): Promise<{ watchlists: WatchlistDTO[] }> {
  return apiFetch("/watchlists");
}

export function fetchWatchlist(id: number): Promise<WatchlistDTO> {
  return apiFetch(`/watchlists/${id}`);
}

export function createWatchlist(name: string, symbols?: string): Promise<WatchlistDTO> {
  const params = symbols ? `?name=${name}&symbols=${symbols}` : `?name=${name}`;
  return apiFetch(`/watchlists${params}`, { method: "POST" });
}

export function updateWatchlist(id: number, data: WatchlistUpdateDTO): Promise<WatchlistDTO> {
  return apiFetch(`/watchlists/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteWatchlist(id: number): Promise<{ success: boolean }> {
  return apiFetch(`/watchlists/${id}`, { method: "DELETE" });
}

export function addWatchlistSymbol(id: number, symbol: string): Promise<WatchlistDTO> {
  return apiFetch(`/watchlists/${id}/symbols?symbol=${symbol}`, { method: "POST" });
}

export function removeWatchlistSymbol(id: number, symbol: string): Promise<WatchlistDTO> {
  return apiFetch(`/watchlists/${id}/symbols/${symbol}`, { method: "DELETE" });
}

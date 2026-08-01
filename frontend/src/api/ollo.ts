import { apiFetch } from "./client"
import type { OLLOResponse, OLLOBriefing, OLLOStatus } from "../types/ollo"

export function greetOLLO(room = "command_deck"): Promise<OLLOResponse> {
  return apiFetch<OLLOResponse>(`/ollo/greet?room=${room}`)
}

export function queryOLLO(query: string, room = "command_deck"): Promise<OLLOResponse> {
  return apiFetch<OLLOResponse>(`/ollo/query?query=${encodeURIComponent(query)}&room=${room}`)
}

export function fetchBriefing(kind = "morning", room = "command_deck"): Promise<OLLOBriefing> {
  return apiFetch<OLLOBriefing>(`/ollo/briefing?kind=${kind}&room=${room}`)
}

export function fetchOLLOStatus(): Promise<OLLOStatus> {
  return apiFetch<OLLOStatus>("/ollo/status")
}

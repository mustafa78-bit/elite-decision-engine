import { apiFetch } from "./client"
import i18n from "../i18n"
import type { OLLOResponse, OLLOBriefing, OLLOStatus } from "../types/ollo"

// OLLO's own replies come from the LLM and follow whatever language the
// founder writes in, but its "AI unavailable" fallback text (shown when the
// AI call itself fails) can't go through the model -- pass the UI's current
// language so that one message is picked from the backend's own small
// en/tr dict (services/ollo/i18n_fallback.py) instead of staying hardcoded
// English regardless of the selected UI language.
function currentLang(): string {
  return i18n.language?.startsWith("tr") ? "tr" : "en"
}

export function greetOLLO(room = "command_deck"): Promise<OLLOResponse> {
  return apiFetch<OLLOResponse>(`/ollo/greet?room=${room}&lang=${currentLang()}`)
}

export function queryOLLO(query: string, room = "command_deck"): Promise<OLLOResponse> {
  return apiFetch<OLLOResponse>(`/ollo/query?query=${encodeURIComponent(query)}&room=${room}&lang=${currentLang()}`, {
    method: "POST",
  })
}

export function fetchBriefing(kind = "morning", room = "command_deck"): Promise<OLLOBriefing> {
  return apiFetch<OLLOBriefing>(`/ollo/briefing?kind=${kind}&room=${room}&lang=${currentLang()}`)
}

export function fetchOLLOStatus(): Promise<OLLOStatus> {
  return apiFetch<OLLOStatus>("/ollo/status")
}

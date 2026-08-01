import { useEffect, useState, useRef } from "react"
import { fetchLatestEvidence } from "../api/evidence"
import { greetOLLO, fetchBriefing, fetchOLLOStatus } from "../api/ollo"
import { fetchAIHealth } from "../api/ai-health"
import { fetchScannerDashboard, type ScannerDashboard } from "../api/scanner"
import { fetchRisk, type RiskData } from "../api/risk"
import { getCouncilStatus, type CouncilStatusData } from "../api/council"
import { fetchPortfolioSummary } from "../api/portfolio_detail"
import { fetchWhaleActivity, type WhaleActivity } from "../api/whale"
import { fetchMarket, type MarketData } from "../api/market"
import type { EvidenceReport } from "../types/evidence"
import type { OLLOResponse, OLLOBriefing, OLLOStatus } from "../types/ollo"
import type { AIHealthResponse } from "../api/ai-health"
import type { PortfolioSummaryDTO } from "../types/api/portfolio"
import type { SubsystemState, SubsystemStatus } from "../types/system"

interface SubsystemsResult {
  scanner: SubsystemState<ScannerDashboard>
  risk: SubsystemState<RiskData>
  council: SubsystemState<CouncilStatusData>
  portfolio: SubsystemState<PortfolioSummaryDTO>
  whale: SubsystemState<WhaleActivity[]>
  market: SubsystemState<MarketData>
  evidence: SubsystemState<EvidenceReport>
  ollo: { greeting: OLLOResponse | null; briefing: OLLOBriefing | null; status: SubsystemState<OLLOStatus> }
  aiHealth: SubsystemState<AIHealthResponse>
  loading: boolean
}

function safeFetch<T>(
  fetcher: () => Promise<T>,
): Promise<SubsystemState<T>> {
  return fetcher()
    .then((data) => ({ status: "ONLINE" as SubsystemStatus, data, error: null }))
    .catch((err: Error) => ({
      status: "OFFLINE" as SubsystemStatus,
      data: null,
      error: err.message,
    }))
}

export function useSubsystems(): SubsystemsResult {
  const [scanner, setScanner] = useState<SubsystemState<ScannerDashboard>>({ status: "UNKNOWN", data: null, error: null })
  const [risk, setRisk] = useState<SubsystemState<RiskData>>({ status: "UNKNOWN", data: null, error: null })
  const [council, setCouncil] = useState<SubsystemState<CouncilStatusData>>({ status: "UNKNOWN", data: null, error: null })
  const [portfolio, setPortfolio] = useState<SubsystemState<PortfolioSummaryDTO>>({ status: "UNKNOWN", data: null, error: null })
  const [whale, setWhale] = useState<SubsystemState<WhaleActivity[]>>({ status: "UNKNOWN", data: null, error: null })
  const [market, setMarket] = useState<SubsystemState<MarketData>>({ status: "UNKNOWN", data: null, error: null })
  const [evidence, setEvidence] = useState<SubsystemState<EvidenceReport>>({ status: "UNKNOWN", data: null, error: null })
  const [olloStatus, setOlloStatus] = useState<SubsystemState<OLLOStatus>>({ status: "UNKNOWN", data: null, error: null })
  const [aiHealth, setAiHealth] = useState<SubsystemState<AIHealthResponse>>({ status: "UNKNOWN", data: null, error: null })
  const [greeting, setGreeting] = useState<OLLOResponse | null>(null)
  const [briefing, setBriefing] = useState<OLLOBriefing | null>(null)
  const [loading, setLoading] = useState(true)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    setLoading(true)

    Promise.all([
      safeFetch(() => fetchLatestEvidence()).then((s) => { if (mountedRef.current) setEvidence(s) }),
      safeFetch(() => fetchOLLOStatus()).then((s) => { if (mountedRef.current) setOlloStatus(s) }),
      safeFetch(() => fetchAIHealth()).then((s) => { if (mountedRef.current) setAiHealth(s) }),
      safeFetch(() => fetchScannerDashboard()).then((s) => { if (mountedRef.current) setScanner(s) }),
      safeFetch(() => fetchRisk()).then((s) => { if (mountedRef.current) setRisk(s) }),
      safeFetch(() => getCouncilStatus()).then((s) => { if (mountedRef.current) setCouncil(s) }),
      safeFetch(() => fetchPortfolioSummary()).then((s) => { if (mountedRef.current) setPortfolio(s) }),
      safeFetch(() => fetchWhaleActivity()).then((s) => { if (mountedRef.current) setWhale(s) }),
      safeFetch(() => fetchMarket()).then((s) => { if (mountedRef.current) setMarket(s) }),
      safeFetch(() => greetOLLO()).then((s) => { if (mountedRef.current && s.data) setGreeting(s.data) }),
      safeFetch(() => fetchBriefing()).then((s) => { if (mountedRef.current && s.data) setBriefing(s.data) }),
    ]).finally(() => {
      if (mountedRef.current) setLoading(false)
    })

    return () => { mountedRef.current = false }
  }, [])

  return {
    scanner,
    risk,
    council,
    portfolio,
    whale,
    market,
    evidence,
    ollo: { greeting, briefing, status: olloStatus },
    aiHealth,
    loading,
  }
}

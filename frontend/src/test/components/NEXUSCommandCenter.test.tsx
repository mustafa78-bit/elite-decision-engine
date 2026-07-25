import { describe, expect, it, vi } from "vitest"
import { render, screen, fireEvent } from "../test-utils"
import CommandDeck from "../../pages/CommandDeck"

// Mock framer-motion to bypass animations in test environment without TDZ/hoisting errors
vi.mock("framer-motion", async () => {
  const React = await import("react")
  return {
    motion: {
      div: React.forwardRef(({ children, className, style, ...props }: any, ref: any) => (
        <div ref={ref} className={className} style={style} {...props}>
          {children}
        </div>
      )),
      span: React.forwardRef(({ children, className, style, ...props }: any, ref: any) => (
        <span ref={ref} className={className} style={style} {...props}>
          {children}
        </span>
      )),
    },
    AnimatePresence: ({ children }: any) => <>{children}</>
  }
})

// Mock fetch / apiClient calls
vi.mock("../../api/client", () => ({
  apiFetch: vi.fn((url: string) => {
    if (url.includes("/explain/")) {
      return Promise.resolve({
        signal_id: 101,
        explanation: {
          explanation: "Strong upward momentum detected with macro support.",
          confidence_level: 0.88,
          expected_rr: 3.2,
          market_regime: "BULLISH_TREND",
          weaknesses: ["Short-term RSI overbought", "Volume resistance"],
          timeline: {
            events: [
              { timestamp: "2026-07-16T08:00:00Z", description: "Signal generated at support" }
            ]
          }
        }
      })
    }
    if (url.includes("/council/evaluate")) {
      return Promise.resolve({
        symbol: "BTC/USDT",
        side: "LONG",
        council_report: {
          symbol: "BTC/USDT",
          timestamp: "2026-07-16T08:00:00Z",
          consensus_direction: "BUY",
          consensus_score: 82,
          agreement_level: "HIGH",
          sources_agreeing: 3,
          sources_disagreeing: 0,
          agent_reports: [
            { agent_name: "Technical Expert", reasoning: ["EMA Cross"], latency_ms: 12 }
          ]
        }
      })
    }
    if (url.includes("/portfolio/full")) {
      return Promise.resolve({
        summary: { total_pnl: 15400, win_rate: 0.68, open_trades: 2, profit_factor: 2.9 },
        distribution: { by_symbol: { "BTC/USDT": 0.6, "ETH/USDT": 0.4 } },
        risk: { value_at_risk: 1.2, max_drawdown: 3.5, sharpe: 3.2 }
      })
    }
    if (url.includes("/scanner/dashboard")) {
      return Promise.resolve({
        symbols_scanned: 42,
        opportunities_found: 7,
        top_opportunities: [
          { rank: 1, symbol: "BTC/USDT", side: "BUY", strategy: "EMA Cross", score: 95, probability: 0.88, risk_score: 2, confidence: 0.9, price: 50000, signals: ["RSI_OVERSOLD"] }
        ],
        top_signals: ["RSI_OVERSOLD", "EMA_GOLDEN_CROSS"],
        market_summary: {},
        intelligence_summary: {},
        timestamp: "2026-07-16T08:00:00Z"
      })
    }
    return Promise.resolve({})
  })
}))

vi.mock("../../api/ollo", () => ({
  queryOLLO: vi.fn(() => Promise.resolve({
    text: "OLLO response: Analysis complete.",
    sections: [{ heading: "Summary", content: "Bullish divergence confirmed." }]
  })),
  fetchBriefing: vi.fn(() => Promise.resolve({
    kind: "morning",
    title: "Tactical Morning Briefing",
    text: "Market indicates institutional accumulation on BTC support levels.",
    timestamp: "2026-07-16T08:00:00Z",
    provider: "anthropic",
    model: "claude-3-opus",
    duration_ms: 1200,
    tokens_in: 80,
    tokens_out: 120
  })),
  fetchOLLOStatus: vi.fn(() => Promise.resolve({
    provider: "anthropic",
    model: "claude-3-5-sonnet",
    current_mission_profile: "ALPHA_RECON",
    current_room: "command_deck",
    ai_health: { connected: true, latency_ms: 45, error: null },
    memory: {},
    available_rooms: ["command_deck"]
  })),
  greetOLLO: vi.fn(() => Promise.resolve({
    text: "Greetings Commander.",
    room: "command_deck",
    timestamp: "2026-07-16T08:00:00Z",
    provider: "anthropic",
    model: "claude-3",
    duration_ms: 500,
    tokens_in: 10,
    tokens_out: 15,
    sections: []
  }))
}))

describe("NEXUS Command Center Workspace Tests", () => {
  it("renders the NEXUS Command Center headers and navigation sectors", async () => {
    render(<CommandDeck />)

    // Header check
    expect(screen.getByText("NEXUS COMMAND CENTER")).toBeInTheDocument()
    expect(screen.getByText(/WORKSTATION ACTIVE/)).toBeInTheDocument()

    // Left Sector Sidebar Tab Options should coexist beautifully
    expect(screen.getByText("HQ COCKPIT")).toBeInTheDocument()
    expect(screen.getByText("MORNING BRIEF")).toBeInTheDocument()
    expect(screen.getByText("OLLO CHAT")).toBeInTheDocument()
    expect(screen.getByText("DECISION INTEL")).toBeInTheDocument()
    expect(screen.getByText("COUNCIL CHAMBER")).toBeInTheDocument()
    expect(screen.getByText("PORTFOLIO INTEL")).toBeInTheDocument()
    expect(screen.getByText("SCANNER RADAR")).toBeInTheDocument()
    expect(screen.getByText("MISSION CONTROL")).toBeInTheDocument()
  })

  it("can navigate and switch tabs smoothly", async () => {
    render(<CommandDeck />)

    // Click MORNING BRIEF
    const morningBriefTab = screen.getByText("MORNING BRIEF").closest("button")
    expect(morningBriefTab).toBeTruthy()
    fireEvent.click(morningBriefTab!)

    // Check Morning Brief renders
    expect(await screen.findByText("MORNING BRIEF & MARKET NARRATIVE")).toBeInTheDocument()

    // Click OLLO CHAT
    const conversationTab = screen.getByText("OLLO CHAT").closest("button")
    fireEvent.click(conversationTab!)
    expect(await screen.findByText("CONVERSATION WORKSPACE")).toBeInTheDocument()
  })

  it("verifies Conversation Workspace user interactions and presets", async () => {
    render(<CommandDeck />)

    // Go to Conversation Tab
    const conversationTab = screen.getByText("OLLO CHAT").closest("button")
    fireEvent.click(conversationTab!)

    // Click prompt preset
    const presetBtn = await screen.findByText("Analyze market risk")
    fireEvent.click(presetBtn)

    // Verify loading and completed mock response
    expect(await screen.findByText("OLLO response: Analysis complete.")).toBeInTheDocument()
    expect(screen.getByText("Bullish divergence confirmed.")).toBeInTheDocument()
  })

  it("verifies Decision Explanation expected metrics and weaknesses", async () => {
    render(<CommandDeck />)

    // Go to Decision Intel
    const explanationTab = screen.getByText("DECISION INTEL").closest("button")
    fireEvent.click(explanationTab!)

    expect(await screen.findByText("EXPLAINABLE AI & DECISION CORRELATIONS")).toBeInTheDocument()

    // Expect expected metrics
    expect(await screen.findByText("Strong upward momentum detected with macro support.")).toBeInTheDocument()
    expect(screen.getByText("Identified Weaknesses & Friction Points")).toBeInTheDocument()
    expect(screen.getByText(/RSI overbought/)).toBeInTheDocument()
    expect(screen.getByText(/3.20/)).toBeInTheDocument() // Expected RR
  })

  it("verifies AI Council consensus evaluating simulator", async () => {
    render(<CommandDeck />)

    // Go to AI Council Tab
    const councilTab = screen.getByText("COUNCIL CHAMBER").closest("button")
    fireEvent.click(councilTab!)

    expect(await screen.findByText("AI COUNCIL CHAMBER & AGENT CONSENSUS")).toBeInTheDocument()

    // Click Evaluate symbol button
    const evalBtn = screen.getByText("EVALUATE SYMBOL")
    fireEvent.click(evalBtn)

    // Expect Consensus Direction and individual Agent audits
    expect(await screen.findByText("CONSENSUS DIRECTION:")).toBeInTheDocument()
    expect(screen.getByText(/AGREEMENT LEVEL/i)).toBeInTheDocument()
    expect(screen.getByText("EMA Cross")).toBeInTheDocument()
  })

  it("verifies Portfolio Intelligence overall stats and allocation gauges", async () => {
    render(<CommandDeck />)

    // Go to Portfolio Intel Tab
    const portfolioTab = screen.getByText("PORTFOLIO INTEL").closest("button")
    fireEvent.click(portfolioTab!)

    expect(await screen.findByText("PORTFOLIO INTELLIGENCE & CAPITAL METRICS")).toBeInTheDocument()

    // Expect overall stats to load successfully
    expect(await screen.findByText("$15,400")).toBeInTheDocument() // Total PNL
    expect(screen.getByText("68%")).toBeInTheDocument() // Win rate
    expect(screen.getByText("2.90")).toBeInTheDocument() // Profit Factor
    expect(screen.getByText("Value-at-Risk (95% 1-Day)")).toBeInTheDocument()
  })

  it("verifies Scanner Intelligence high-conviction opportunities table", async () => {
    render(<CommandDeck />)

    // Go to Scanner Radar
    const scannerTab = screen.getByText("SCANNER RADAR").closest("button")
    fireEvent.click(scannerTab!)

    expect(await screen.findByText("SCANNER INTELLIGENCE & SURVEILLANCE FEED")).toBeInTheDocument()

    // Fallback/loaded opportunities
    expect(await screen.findByText("High-Conviction Scanned Opportunities Radar")).toBeInTheDocument()
    expect(screen.getByText("RSI_OVERSOLD")).toBeInTheDocument()
  })

  it("verifies Mission Control subsystems and offline forced overrides", async () => {
    render(<CommandDeck />)

    // Go to Mission Control Tab
    const controlsTab = screen.getByText("MISSION CONTROL").closest("button")
    fireEvent.click(controlsTab!)

    expect(await screen.findByText("MISSION CONTROL & SUBSYSTEM MANAGER")).toBeInTheDocument()
    expect(screen.getByText("Interactive Subsystem Override Switches")).toBeInTheDocument()

    // Verify offline forced overrides trigger
    const overrideBtn = screen.getAllByText("FORCE OFFLINE")[0]
    fireEvent.click(overrideBtn)

    // Subsystem should report OFFLINE
    expect(screen.getByText("FORCED OFFLINE")).toBeInTheDocument()
  })

  it("verifies keyboard accessibility and tab index order elements", async () => {
    render(<CommandDeck />)

    // Focus order and role attributes should be well-formed
    const hqCockpitTab = screen.getByText("HQ COCKPIT").closest("button")

    // Trigger keyboard actions
    hqCockpitTab?.focus()
    expect(document.activeElement).toBe(hqCockpitTab)
  })
})

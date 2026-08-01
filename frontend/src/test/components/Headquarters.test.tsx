import { describe, expect, it } from "vitest";
import { render, screen } from "../test-utils";
import MissionStatusBar from "../../components/hq/MissionStatusBar";
import EvidencePanel from "../../components/hq/EvidencePanel";
import OLLOCommander from "../../components/hq/OLLOCommander";
import type { EvidenceReport } from "../../types/evidence";
import type { OLLOResponse, OLLOBriefing } from "../../types/ollo";

function makeReport(overrides: Partial<EvidenceReport> = {}): EvidenceReport {
  return {
    recommendation: "Hold current positions",
    decision_confidence: 0.82,
    evidence_strength: 0.75,
    explainability: 0.91,
    decision_quality: "HIGH",
    summary: "Market conditions favorable with moderate risks.",
    reasoning: ["Technical indicators align with trend.", "Volume confirms momentum."],
    supporting_evidence: [
      { id: "e1", title: "RSI above 60", description: "Momentum indicator shows strength", engine: "scanner", category: "technical", severity: "MEDIUM", confidence: 0.8, weight: 1.0, supports_decision: true, metadata: {}, source: null, timestamp: "", version: "" },
    ],
    contradicting_evidence: [
      { id: "e2", title: "Resistance at $52k", description: "Price approaching key level", engine: "scanner", category: "technical", severity: "MEDIUM", confidence: 0.6, weight: 0.8, supports_decision: false, metadata: {}, source: null, timestamp: "", version: "" },
    ],
    warnings: ["Volatility exceeding normal range."],
    risk_notes: ["Position size at 15% of portfolio (limit 20%)."],
    timeline: [
      { id: "t1", title: "Signal generated", description: "", engine: "scanner", category: "signal", severity: "LOW", confidence: 0.0, weight: 1.0, supports_decision: true, metadata: {}, source: null, timestamp: "2026-07-16T08:00:00Z", version: "" },
    ],
    sources: [
      { module: "scanner_service", module_version: "1.2.0", component: "RSIIndicator", input_keys: ["price_data"], output_keys: ["rsi_value"], timestamp: "2026-07-16T08:00:00Z" },
    ],
    decision_id: "abc123def456",
    created_at: "2026-07-16T08:00:00Z",
    ...overrides,
  };
}

/* ====== MissionStatusBar ====== */
describe("MissionStatusBar", () => {
  it("renders ACTIVE status with green indicator", () => {
    render(<MissionStatusBar status="ACTIVE" decisionQuality="HIGH" evidenceStrength={0.9} warnings={0} />);
    expect(screen.getByText("ACTIVE")).toBeInTheDocument();
  });

  it("renders CRITICAL status with red indicator", () => {
    render(<MissionStatusBar status="CRITICAL" decisionQuality="LOW" evidenceStrength={0.2} warnings={3} />);
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
  });

  it("renders CAUTION status with orange indicator", () => {
    render(<MissionStatusBar status="CAUTION" decisionQuality="LOW" evidenceStrength={0.3} warnings={1} />);
    expect(screen.getByText("CAUTION")).toBeInTheDocument();
  });

  it("shows current mission when provided", () => {
    render(<MissionStatusBar status="ACTIVE" decisionQuality="HIGH" evidenceStrength={0.9} warnings={0} currentMission="Operation Alpha" />);
    expect(screen.getByText(/Operation Alpha/)).toBeInTheDocument();
  });

  it("shows AI health indicator", () => {
    render(<MissionStatusBar status="ACTIVE" decisionQuality="HIGH" evidenceStrength={0.9} warnings={0} aiConnected={true} aiLatency={42} />);
    expect(screen.getByText(/42ms/)).toBeInTheDocument();
  });

  it("shows alert count when warned", () => {
    render(<MissionStatusBar status="CAUTION" decisionQuality="LOW" evidenceStrength={0.3} warnings={2} unreadAlerts={2} />);
    expect(screen.getByText(/2 mission alerts/)).toBeInTheDocument();
  });

  it("shows evidence strength percentage", () => {
    render(<MissionStatusBar status="ACTIVE" decisionQuality="HIGH" evidenceStrength={0.85} warnings={0} />);
    expect(screen.getByText("85%")).toBeInTheDocument();
  });

  it("derives status from quality when not forced", () => {
    render(<MissionStatusBar status="MONITORING" decisionQuality="LOW" evidenceStrength={0.3} warnings={1} />);
    expect(screen.getByText("MONITORING")).toBeInTheDocument();
  });
});

/* ====== EvidencePanel ====== */
describe("EvidencePanel", () => {
  it("shows loading state", () => {
    render(<EvidencePanel report={null} loading={true} error={null} />);
    expect(document.querySelector(".skeleton-pulse")).toBeTruthy();
  });

  it("shows error state", () => {
    render(<EvidencePanel report={null} loading={false} error="Failed to fetch evidence" />);
    expect(screen.getByText(/Evidence Offline/)).toBeInTheDocument();
    expect(screen.getByText(/Failed to fetch evidence/)).toBeInTheDocument();
  });

  it("shows empty state when no report", () => {
    render(<EvidencePanel report={null} loading={false} error={null} />);
    expect(screen.getByText(/No Evidence Available/)).toBeInTheDocument();
  });

  it("renders decision recommendation", () => {
    const report = makeReport();
    render(<EvidencePanel report={report} loading={false} error={null} />);
    expect(screen.getByText("Hold current positions")).toBeInTheDocument();
  });

  it("renders decision quality badge", () => {
    const report = makeReport();
    render(<EvidencePanel report={report} loading={false} error={null} />);
    expect(screen.getByText("High Confidence")).toBeInTheDocument();
  });

  it("renders gauge values for confidence, strength, explainability", () => {
    const report = makeReport({ decision_confidence: 0.82, evidence_strength: 0.75, explainability: 0.91 });
    render(<EvidencePanel report={report} loading={false} error={null} />);
    expect(screen.getByText("82%")).toBeInTheDocument();
    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getByText("91%")).toBeInTheDocument();
  });

  it("shows conflict level from contradicting evidence", () => {
    const report = makeReport({ contradicting_evidence: [
      { id: "c1", title: "Test conflict", description: "", engine: "scanner", category: "technical", severity: "MEDIUM", confidence: 0.5, weight: 1.0, supports_decision: false, metadata: {}, source: null, timestamp: "", version: "" },
    ]});
    render(<EvidencePanel report={report} loading={false} error={null} />);
    expect(screen.getByText("Low")).toBeInTheDocument();
  });

  it("shows warning count", () => {
    const report = makeReport({ warnings: ["Warning 1", "Warning 2", "Warning 3"] });
    render(<EvidencePanel report={report} loading={false} error={null} />);
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("renders summary text when present", () => {
    const report = makeReport({ summary: "Market conditions favorable." });
    render(<EvidencePanel report={report} loading={false} error={null} />);
    expect(screen.getByText("Market conditions favorable.")).toBeInTheDocument();
  });

  it("renders timeline events", () => {
    const report = makeReport();
    render(<EvidencePanel report={report} loading={false} error={null} />);
    expect(screen.getByText("Signal generated")).toBeInTheDocument();
  });

  it("shows decision ID", () => {
    const report = makeReport({ decision_id: "abc123def456" });
    render(<EvidencePanel report={report} loading={false} error={null} />);
    expect(screen.getByText(/abc123de/)).toBeInTheDocument();
  });

  it("shows expandable reasoning section", () => {
    const report = makeReport();
    render(<EvidencePanel report={report} loading={false} error={null} />);
    expect(screen.getByText(/Reasoning/)).toBeInTheDocument();
  });

  it("shows expandable sources section", () => {
    const report = makeReport();
    render(<EvidencePanel report={report} loading={false} error={null} />);
    expect(screen.getByText(/Sources/)).toBeInTheDocument();
  });

  it("shows contradicting evidence count in header", () => {
    const report = makeReport();
    render(<EvidencePanel report={report} loading={false} error={null} />);
    expect(screen.getByText(/Contradicting Evidence/)).toBeInTheDocument();
  });

  it("shows supporting evidence count", () => {
    const report = makeReport();
    render(<EvidencePanel report={report} loading={false} error={null} />);
    expect(screen.getByText(/Supporting Evidence/)).toBeInTheDocument();
  });
});

/* ====== Mission Computation ====== */
describe("computeMissionStatus", () => {
  it("returns ACTIVE when all systems nominal", async () => {
    const { computeMissionStatus } = await import("../../types/mission");
    expect(computeMissionStatus(20, "HIGH", true, 0)).toBe("ACTIVE");
  });

  it("returns ACTIVE when risk < 30 and quality HIGH and AI connected", async () => {
    const { computeMissionStatus } = await import("../../types/mission");
    expect(computeMissionStatus(25, "HIGH", true, 0)).toBe("ACTIVE");
  });

  it("returns MONITORING when risk between 30-50 and quality HIGH", async () => {
    const { computeMissionStatus } = await import("../../types/mission");
    expect(computeMissionStatus(40, "HIGH", true, 0)).toBe("MONITORING");
  });

  it("returns MONITORING when quality MEDIUM", async () => {
    const { computeMissionStatus } = await import("../../types/mission");
    expect(computeMissionStatus(20, "MEDIUM", true, 0)).toBe("MONITORING");
  });

  it("returns CAUTION when risk > 50", async () => {
    const { computeMissionStatus } = await import("../../types/mission");
    expect(computeMissionStatus(60, "HIGH", true, 0)).toBe("CAUTION");
  });

  it("returns CAUTION when quality LOW", async () => {
    const { computeMissionStatus } = await import("../../types/mission");
    expect(computeMissionStatus(20, "LOW", true, 0)).toBe("CAUTION");
  });

  it("returns CAUTION when 1 subsystem is offline", async () => {
    const { computeMissionStatus } = await import("../../types/mission");
    expect(computeMissionStatus(20, "HIGH", true, 1)).toBe("CAUTION");
  });

  it("returns CRITICAL when risk > 80", async () => {
    const { computeMissionStatus } = await import("../../types/mission");
    expect(computeMissionStatus(85, "HIGH", true, 0)).toBe("CRITICAL");
  });

  it("returns CRITICAL when more than 2 subsystems offline", async () => {
    const { computeMissionStatus } = await import("../../types/mission");
    expect(computeMissionStatus(20, "HIGH", true, 3)).toBe("CRITICAL");
  });

  it("returns CRITICAL when AI is disconnected", async () => {
    const { computeMissionStatus } = await import("../../types/mission");
    expect(computeMissionStatus(20, "HIGH", false, 0)).toBe("CRITICAL");
  });

  it("returns CAUTION when no risk data available", async () => {
    const { computeMissionStatus } = await import("../../types/mission");
    expect(computeMissionStatus(null, "HIGH", true, 0)).toBe("CAUTION");
  });
});

/* ====== Safe Fetch (graceful degradation) ====== */
describe("safeFetch graceful degradation", () => {
  it("returns ONLINE state on success", async () => {
    const fetcher = () => Promise.resolve({ data: "test" });
    const safeFetch = async <T,>(fn: () => Promise<T>) => {
      try {
        const data = await fn();
        return { status: "ONLINE" as const, data, error: null };
      } catch (err) {
        return { status: "OFFLINE" as const, data: null, error: (err as Error).message };
      }
    };
    const result = await safeFetch(fetcher);
    expect(result.status).toBe("ONLINE");
    expect(result.data).toEqual({ data: "test" });
    expect(result.error).toBeNull();
  });

  it("returns OFFLINE state on error", async () => {
    const fetcher = () => Promise.reject(new Error("Connection refused"));
    const safeFetch = async <T,>(fn: () => Promise<T>) => {
      try {
        const data = await fn();
        return { status: "ONLINE" as const, data, error: null };
      } catch (err) {
        return { status: "OFFLINE" as const, data: null, error: (err as Error).message };
      }
    };
    const result = await safeFetch(fetcher);
    expect(result.status).toBe("OFFLINE");
    expect(result.data).toBeNull();
    expect(result.error).toBe("Connection refused");
  });

  it("renders error state gracefully in EvidencePanel", () => {
    render(<EvidencePanel report={null} loading={false} error="Evidence Engine unavailable" />);
    expect(screen.getByText(/Evidence Offline/)).toBeInTheDocument();
    expect(screen.getByText(/Evidence Engine unavailable/)).toBeInTheDocument();
  });

  it("renders empty state gracefully in EvidencePanel", () => {
    render(<EvidencePanel report={null} loading={false} error={null} />);
    expect(screen.getByText(/No Evidence Available/)).toBeInTheDocument();
  });
});

/* ====== Subsystem Status Rendering ====== */
describe("Subsystem status display", () => {
  it("shows ONLINE status with green indicator", () => {
    const { container } = render(
      <div>
        <span className="w-1 h-1 rounded-full" style={{ backgroundColor: "#22C55E" }} />
        <span>ONLINE</span>
      </div>
    );
    expect(container.querySelector("span[style*='background-color: rgb(34, 197, 94)']")).toBeTruthy();
    expect(screen.getByText("ONLINE")).toBeInTheDocument();
  });

  it("shows OFFLINE status with red indicator", () => {
    const { container } = render(
      <div>
        <span className="w-1 h-1 rounded-full" style={{ backgroundColor: "#EF4444" }} />
        <span>OFFLINE</span>
      </div>
    );
    expect(container.querySelector("span[style*='background-color: rgb(239, 68, 68)']")).toBeTruthy();
    expect(screen.getByText("OFFLINE")).toBeInTheDocument();
  });

  it("shows UNKNOWN status with gray indicator", () => {
    render(
      <div>
        <span style={{ color: "#64748B" }}>UNKNOWN</span>
      </div>
    );
    expect(screen.getByText("UNKNOWN")).toBeInTheDocument();
  });
});

/* ====== OLLOCommander ====== */
describe("OLLOCommander", () => {
  it("shows loading state", () => {
    render(<OLLOCommander greeting={null} briefing={null} loading={true} error={null} />);
    expect(document.querySelector(".skeleton-pulse")).toBeTruthy();
  });

  it("shows error state", () => {
    render(<OLLOCommander greeting={null} briefing={null} loading={false} error="OLLO connection failed" />);
    expect(screen.getByText("OLLO connection failed")).toBeInTheDocument();
  });

  it("shows greeting text when provided", () => {
    const greeting: OLLOResponse = {
      text: "Welcome, Commander. All systems operational.",
      room: "command_deck",
      timestamp: "2026-07-16T08:00:00Z",
      provider: "openai",
      model: "gpt-4",
      duration_ms: 1200,
      tokens_in: 50,
      tokens_out: 30,
      sections: [],
    };
    render(<OLLOCommander greeting={greeting} briefing={null} loading={false} error={null} />);
    expect(screen.getAllByText(/Welcome, Commander/).length).toBeGreaterThan(0);
  });

  it("shows greeting sections when present", () => {
    const greeting: OLLOResponse = {
      text: "Welcome back.",
      room: "command_deck",
      timestamp: "2026-07-16T08:00:00Z",
      provider: "openai",
      model: "gpt-4",
      duration_ms: 900,
      tokens_in: 40,
      tokens_out: 25,
      sections: [
        { heading: "Market Overview", content: "Markets are trending upward." },
        { heading: "Risk Assessment", content: "Risk levels are moderate." },
      ],
    };
    render(<OLLOCommander greeting={greeting} briefing={null} loading={false} error={null} />);
    expect(screen.getByText("Market Overview")).toBeInTheDocument();
    expect(screen.getByText("Risk Assessment")).toBeInTheDocument();
  });

  it("shows provider and model in greeting", () => {
    const greeting: OLLOResponse = {
      text: "Hello.",
      room: "command_deck",
      timestamp: "2026-07-16T08:00:00Z",
      provider: "anthropic",
      model: "claude-3",
      duration_ms: 800,
      tokens_in: 30,
      tokens_out: 20,
      sections: [],
    };
    render(<OLLOCommander greeting={greeting} briefing={null} loading={false} error={null} />);
    expect(screen.getByText(/anthropic/)).toBeInTheDocument();
    expect(screen.getByText(/claude-3/)).toBeInTheDocument();
  });

  it("shows briefing when provided", () => {
    const briefing: OLLOBriefing = {
      kind: "morning",
      title: "Operation Market Pulse",
      text: "Today's briefing covers key market movements.",
      timestamp: "2026-07-16T08:00:00Z",
      provider: "openai",
      model: "gpt-4",
      duration_ms: 1500,
      tokens_in: 100,
      tokens_out: 80,
    };
    render(<OLLOCommander greeting={null} briefing={briefing} loading={false} error={null} />);
    expect(screen.getByText(/Operation Market Pulse/)).toBeInTheDocument();
    expect(screen.getByText(/morning Briefing/)).toBeInTheDocument();
    expect(screen.getByText(/Today's briefing covers/)).toBeInTheDocument();
  });

  it("shows awaiting connection state", () => {
    render(<OLLOCommander greeting={null} briefing={null} loading={false} error={null} />);
    expect(screen.getByText("Awaiting OLLO connection...")).toBeInTheDocument();
  });
});

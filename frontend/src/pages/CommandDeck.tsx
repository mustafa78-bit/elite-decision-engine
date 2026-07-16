import { useMemo } from "react"
import { useSubsystems } from "../hooks/useSubsystems"
import { computeMissionStatus, type MissionStatus } from "../types/mission"
import EvidencePanel from "../components/hq/EvidencePanel"
import MissionStatusBar from "../components/hq/MissionStatusBar"
import OLLOCommander from "../components/hq/OLLOCommander"
import SubsystemRow from "../components/hq/SubsystemRow"

export default function CommandDeck() {
  const {
    scanner, risk, council, portfolio, whale, market, evidence,
    ollo, aiHealth, loading,
  } = useSubsystems()

  const decisionQuality = evidence.data?.decision_quality ?? null
  const evidenceStrength = evidence.data?.evidence_strength ?? 0
  const warnings = evidence.data?.warnings ?? []
  const riskScore = risk.data?.risk_score ?? null
  const aiConnected = aiHealth.data?.ollo.connected ?? ollo.status.data?.ai_health.connected ?? null
  const aiLatency = aiHealth.data?.ollo.latency_ms ?? ollo.status.data?.ai_health.latency_ms

  const offlineCount = [scanner, risk, council, portfolio, whale, market, evidence, ollo.status, aiHealth]
    .filter((s) => s.status === "OFFLINE").length

  const missionStatus: MissionStatus = computeMissionStatus(riskScore, decisionQuality, aiConnected, offlineCount)

  const currentMission = ollo.briefing?.title || ollo.status.data?.current_mission_profile?.replace(/_/g, " ") || undefined
  const scannerCount = scanner.data?.opportunities_found ?? null
  const portfolioPnl = portfolio.data?.total_pnl ?? null
  const portfolioWinRate = portfolio.data?.win_rate ?? null
  const whaleCount = whale.data?.length ?? null
  const councilAgents = council.data?.agent_count ?? null
  const marketPrice = market.data?.price ?? null
  const marketRegime = market.data?.regime ?? null

  return (
    <div className="min-h-full flex flex-col">
      {/* Mission Status Bar */}
      <MissionStatusBar
        status={missionStatus}
        decisionQuality={decisionQuality ?? "UNKNOWN"}
        evidenceStrength={evidenceStrength}
        warnings={warnings.length}
        currentMission={currentMission}
        aiConnected={aiConnected ?? undefined}
        aiLatency={aiLatency}
        unreadAlerts={warnings.length}
        systemStatus={aiHealth.data?.status?.toUpperCase()}
      />

      {/* Situation Summary */}
      {evidence.data?.summary && (
        <div className="px-4 py-2 border-b border-[var(--border-subtle)]/30">
          <div className="flex items-start gap-2">
            <span className="text-[9px] font-medium text-[var(--text-muted)] uppercase tracking-[0.1em] shrink-0 mt-0.5">
              Situation
            </span>
            <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
              {evidence.data.summary}
            </p>
          </div>
        </div>
      )}

      {/* Main Grid */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 p-4 overflow-y-auto">
        {/* Left Column */}
        <div className="lg:col-span-5 space-y-4">
          {/* OLLO Commander */}
          <div className="glass-card overflow-hidden">
            <OLLOCommander
              greeting={ollo.greeting}
              briefing={ollo.briefing}
              loading={loading && !ollo.greeting}
              error={ollo.status.error}
            />
          </div>

          {/* Current Mission */}
          {ollo.briefing && (
            <div className="glass-card p-4">
              <div className="text-[9px] font-medium text-[var(--accent-blue)] uppercase tracking-[0.1em] mb-2">
                Current Mission
              </div>
              <div className="text-[10px] font-medium text-[var(--text-primary)] mb-1">
                {ollo.briefing.title}
              </div>
              <p className="text-[10px] text-[var(--text-secondary)] leading-relaxed">
                {ollo.briefing.text}
              </p>
              <div className="mt-2 flex items-center gap-2 text-[8px] font-mono text-[var(--text-muted)]">
                <span>{ollo.briefing.kind} briefing</span>
                <span>·</span>
                <span>{ollo.briefing.provider}</span>
              </div>
            </div>
          )}

          {/* AI Health */}
          <div className="glass-card p-4">
            <div className="text-[9px] font-medium text-[var(--text-muted)] uppercase tracking-[0.1em] mb-3">
              AI Health
            </div>
            <div className="space-y-1">
              {loading && !aiHealth.data ? (
                <div className="h-2 skeleton-pulse w-full" />
              ) : (
                <>
                  <SubsystemRow label="OLLO Commander" status={aiHealth.data?.ollo.connected ? "ONLINE" : "OFFLINE"} detail={aiHealth.data?.ollo.latency_ms ? `${aiHealth.data.ollo.latency_ms.toFixed(0)}ms` : undefined} />
                  <SubsystemRow label="Evidence Engine" status={aiHealth.data?.evidence_engine.available ? "ONLINE" : "OFFLINE"} />
                  {Object.entries(aiHealth.data?.providers || {}).map(([name, p]) => (
                    <SubsystemRow key={name} label={name.charAt(0).toUpperCase() + name.slice(1)} status={p.connected ? "ONLINE" : "OFFLINE"} />
                  ))}
                  <SubsystemRow label="System" status={aiHealth.data?.status === "healthy" ? "ONLINE" : aiHealth.data?.status ? "DEGRADED" : "UNKNOWN"} />
                </>
              )}
            </div>
          </div>

          {/* Portfolio Snapshot */}
          <div className="glass-card p-4">
            <div className="text-[9px] font-medium text-[var(--text-muted)] uppercase tracking-[0.1em] mb-2">
              Portfolio Vault
            </div>
            {portfolio.error ? (
              <SubsystemRow label="Portfolio" status="OFFLINE" detail="Unavailable" />
            ) : portfolio.data ? (
              <div className="space-y-1.5 text-[10px] font-mono">
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">PnL</span>
                  <span className={portfolioPnl !== null && portfolioPnl >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}>
                    {portfolioPnl !== null ? `${portfolioPnl >= 0 ? "+" : ""}$${portfolioPnl.toLocaleString()}` : "--"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Win Rate</span>
                  <span className="text-[var(--text-primary)]">
                    {portfolioWinRate !== null ? `${(portfolioWinRate * 100).toFixed(1)}%` : "--"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Open Trades</span>
                  <span className="text-[var(--text-primary)]">{portfolio.data?.open_trades ?? "--"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Total Trades</span>
                  <span className="text-[var(--text-primary)]">{portfolio.data?.total_trades ?? "--"}</span>
                </div>
              </div>
            ) : (
              <div className="h-2 skeleton-pulse w-full" />
            )}
          </div>

          {/* Council Status */}
          <div className="glass-card p-4">
            <div className="text-[9px] font-medium text-[var(--accent-purple)] uppercase tracking-[0.1em] mb-2">
              AI Council Chamber
            </div>
            {council.error ? (
              <SubsystemRow label="Council" status="OFFLINE" detail="Unavailable" />
            ) : council.data ? (
              <div className="space-y-1.5 text-[10px] font-mono">
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Agents</span>
                  <span className="text-[var(--text-primary)]">{councilAgents}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Active</span>
                  <span className="text-[var(--text-primary)]">{council.data.agents.length} agents</span>
                </div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {council.data.agents.slice(0, 4).map((agent) => (
                    <span key={agent} className="px-1.5 py-0.5 text-[8px] font-mono rounded" style={{ backgroundColor: "rgba(139, 92, 246, 0.1)", color: "#8B5CF6" }}>
                      {agent}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <div className="h-2 skeleton-pulse w-full" />
            )}
          </div>
        </div>

        {/* Right Column */}
        <div className="lg:col-span-7 space-y-4">
          {/* Evidence Panel */}
          <EvidencePanel
            report={evidence.data}
            loading={loading && !evidence.data}
            error={evidence.error}
          />

          {/* Scanner + Market + Whale row */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Scanner Room */}
            <div className="glass-card p-4">
              <div className="text-[9px] font-medium text-[var(--accent-cyan)] uppercase tracking-[0.1em] mb-2">
                Scanner Room
              </div>
              {scanner.error ? (
                <SubsystemRow label="Scanner" status="OFFLINE" />
              ) : scanner.data ? (
                <div className="space-y-1.5 text-[10px] font-mono">
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Symbols Scanned</span>
                    <span className="text-[var(--text-primary)]">{scanner.data.symbols_scanned}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Opportunities</span>
                    <span className="text-[var(--text-primary)]">{scannerCount}</span>
                  </div>
                  {scanner.data.top_opportunities && scanner.data.top_opportunities.length > 0 && (
                    <div className="text-[8px] text-[var(--text-muted)] mt-1">
                      Top: {scanner.data.top_opportunities[0].symbol} ({scanner.data.top_opportunities[0].score.toFixed(0)})
                    </div>
                  )}
                </div>
              ) : (
                <div className="h-2 skeleton-pulse w-full" />
              )}
            </div>

            {/* Market Room */}
            <div className="glass-card p-4">
              <div className="text-[9px] font-medium text-[var(--accent-blue)] uppercase tracking-[0.1em] mb-2">
                Market Room
              </div>
              {market.error ? (
                <SubsystemRow label="Market" status="OFFLINE" />
              ) : market.data ? (
                <div className="space-y-1.5 text-[10px] font-mono">
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Price</span>
                    <span className="text-[var(--text-primary)]">${marketPrice?.toLocaleString() ?? "--"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Regime</span>
                    <span className="text-[var(--text-primary)]">{marketRegime ?? "--"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">RSI</span>
                    <span className="text-[var(--text-primary)]">{market.data.rsi?.toFixed(0) ?? "--"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Volatility</span>
                    <span className="text-[var(--text-primary)]">{(market.data.volatility * 100).toFixed(1)}%</span>
                  </div>
                </div>
              ) : (
                <div className="h-2 skeleton-pulse w-full" />
              )}
            </div>

            {/* Whale Intelligence */}
            <div className="glass-card p-4">
              <div className="text-[9px] font-medium text-[var(--accent-cyan)] uppercase tracking-[0.1em] mb-2" style={{ color: "#0E7490" }}>
                Whale Intelligence
              </div>
              {whale.error ? (
                <SubsystemRow label="Whale" status="OFFLINE" />
              ) : whale.data ? (
                <div className="space-y-1.5 text-[10px] font-mono">
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Recent Activity</span>
                    <span className="text-[var(--text-primary)]">{whaleCount} events</span>
                  </div>
                  {whale.data.length > 0 && (
                    <div className="text-[8px] text-[var(--text-muted)] mt-1 max-h-[60px] overflow-y-auto space-y-0.5">
                      {whale.data.slice(0, 3).map((w, i) => (
                        <div key={i} className="truncate">{w.symbol}: {w.type}</div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="h-2 skeleton-pulse w-full" />
              )}
            </div>
          </div>

          {/* OLLO System Status */}
          {ollo.status.data && (
            <div className="glass-card p-4">
              <div className="text-[9px] font-medium text-[var(--text-muted)] uppercase tracking-[0.1em] mb-2">
                OLLO System Status
              </div>
              <div className="space-y-1.5 text-[10px] font-mono">
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Mission Profile</span>
                  <span className="text-[var(--text-primary)] capitalize">{ollo.status.data.current_mission_profile.replace(/_/g, " ")}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Provider</span>
                  <span className="text-[var(--text-primary)]">{ollo.status.data.provider}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Model</span>
                  <span className="text-[var(--text-primary)]">{ollo.status.data.model}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">Current Room</span>
                  <span className="text-[var(--text-primary)] capitalize">{ollo.status.data.current_room.replace(/_/g, " ")}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-muted)]">AI Connection</span>
                  <span style={{ color: ollo.status.data.ai_health.connected ? "#22C55E" : "#EF4444" }}>
                    {ollo.status.data.ai_health.connected ? "Connected" : "Disconnected"}
                  </span>
                </div>
                {ollo.status.data.ai_health.connected && (
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Latency</span>
                    <span className="text-[var(--text-primary)]">{ollo.status.data.ai_health.latency_ms.toFixed(0)}ms</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Warnings */}
          {warnings.length > 0 && (
            <div className="glass-card p-4" style={{ borderColor: "rgba(249, 115, 22, 0.2)" }}>
              <div className="flex items-center gap-2 mb-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-yellow)]" />
                <span className="text-[10px] font-medium text-[var(--accent-yellow)] uppercase tracking-[0.1em]">
                  Warnings ({warnings.length})
                </span>
              </div>
              <ul className="space-y-1">
                {warnings.map((w, i) => (
                  <li key={i} className="text-[11px] text-[var(--text-secondary)] leading-relaxed flex items-start gap-1.5">
                    <span className="text-[var(--accent-yellow)] mt-0.5 shrink-0">!</span>
                    {w}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Risk Notes */}
          {evidence.data?.risk_notes && evidence.data.risk_notes.length > 0 && (
            <div className="glass-card p-4" style={{ borderColor: "rgba(239, 68, 68, 0.2)" }}>
              <div className="flex items-center gap-2 mb-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-red)]" />
                <span className="text-[10px] font-medium text-[var(--accent-red)] uppercase tracking-[0.1em]">
                  Risk Notes ({evidence.data.risk_notes.length})
                </span>
              </div>
              <ul className="space-y-1">
                {evidence.data.risk_notes.map((r, i) => (
                  <li key={i} className="text-[11px] text-[var(--text-secondary)] leading-relaxed flex items-start gap-1.5">
                    <span className="text-[var(--accent-red)] mt-0.5 shrink-0">▲</span>
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

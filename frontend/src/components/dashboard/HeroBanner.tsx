import { useApi } from "../../hooks/useApi";
import { fetchHeroBanner } from "../../api/widgets";
import type { HeroBannerDTO } from "../../types/api/widget";
import AIAvatar from "./AIAvatar";

const DECISION_STYLES: Record<string, { color: string; glow: string }> = {
  BUY: { color: "var(--accent-green)", glow: "rgba(34,197,94,0.5)" },
  SELL: { color: "var(--accent-red)", glow: "rgba(239,68,68,0.5)" },
  HOLD: { color: "var(--accent-yellow)", glow: "rgba(250,204,21,0.35)" },
  WAIT: { color: "var(--accent-yellow)", glow: "rgba(250,204,21,0.35)" },
};

const REGIME_LABELS: Record<string, string> = {
  TREND: "TRENDING", DOWNTREND: "DOWNTREND", RANGE: "RANGING",
  RECOVERY: "RECOVERING", DEAD: "FLAT",
};
const REGIME_COLORS: Record<string, string> = {
  TREND: "#22C55E", DOWNTREND: "#EF4444", RANGE: "#FACC15",
  RECOVERY: "#22C55E", DEAD: "#64748B",
};

function greeting(): string {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

function buildBriefing(data: HeroBannerDTO): string[] {
  if (!data.symbol) return [];
  const lines: string[] = [];
  if (data.market_regime) {
    const r = (REGIME_LABELS[data.market_regime] ?? data.market_regime).toLowerCase();
    lines.push(`Market conditions are ${r}.`);
  }
  if (data.reasons.length > 0) lines.push(data.reasons.slice(0, 2).join(" "));
  return lines;
}

function formatUSD(v: number): string {
  if (v === 0) return "$0.00";
  return `$${v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function Cell({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[9px] font-medium tracking-[0.08em]" style={{ color: "var(--text-muted)" }}>{label}</span>
      <span className="text-[13px] font-semibold font-mono tabular-nums" style={color ? { color } : { color: "var(--text-primary)" }}>
        {value}
      </span>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="w-full rounded-[20px] overflow-hidden" style={{ background: "linear-gradient(135deg, #101827 0%, #0C1422 100%)", border: "1px solid #243244", boxShadow: "0 8px 32px rgba(0,0,0,0.3)" }}>
      <div className="h-[3px] w-full" style={{ background: "linear-gradient(to right, rgba(139,92,246,0.4), transparent)" }} />
      <div className="p-10 space-y-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full" style={{ background: "rgba(255,255,255,0.04)", border: "1px solid #243244" }} />
          <div className="space-y-2">
            <div className="h-3 w-28 rounded skeleton-pulse" style={{ background: "#243244" }} />
            <div className="h-2.5 w-20 rounded skeleton-pulse" style={{ background: "#1E293B" }} />
          </div>
        </div>
        <div className="space-y-2.5">
          <div className="h-3 w-full rounded skeleton-pulse" style={{ background: "#243244" }} />
          <div className="h-3 w-3/4 rounded skeleton-pulse" style={{ background: "#1E293B" }} />
          <div className="h-3 w-1/2 rounded skeleton-pulse" style={{ background: "#1E293B" }} />
        </div>
      </div>
    </div>
  );
}

export default function HeroBanner() {
  const { data, loading, error, refetch } = useApi(fetchHeroBanner);

  const style = data ? DECISION_STYLES[data.decision] || DECISION_STYLES.WAIT : DECISION_STYLES.WAIT;

  if (loading && !data) return <LoadingSkeleton />;

  if (error) {
    return (
      <div className="w-full rounded-[20px] overflow-hidden glass-card" style={{ background: "linear-gradient(135deg, #101827 0%, #0C1422 100%)" }}>
        <div className="h-[3px] w-full" style={{ background: "linear-gradient(to right, rgba(239,68,68,0.4), transparent)" }} />
        <div className="p-10 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <AIAvatar size={32} />
            <span className="text-[12px] font-mono" style={{ color: "var(--accent-red)" }}>{error}</span>
          </div>
          <button
            onClick={refetch}
            className="text-[10px] font-mono px-3 py-1.5 rounded-lg transition-all"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid #243244", color: "var(--text-muted)", cursor: "pointer" }}
            onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(255,255,255,0.08)"; e.currentTarget.style.color = "#F1F5F9"; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(255,255,255,0.04)"; e.currentTarget.style.color = "#64748B"; }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!data || !data.symbol) {
    return (
      <div className="w-full rounded-[20px] overflow-hidden glass-card" style={{ background: "linear-gradient(135deg, #101827 0%, #0C1422 100%)" }}>
        <div className="h-[3px] w-full" style={{ background: "linear-gradient(to right, rgba(139,92,246,0.3), transparent)" }} />
        <div className="p-14 flex flex-col items-center justify-center gap-5 text-center min-h-[300px]">
          <AIAvatar size={56} />
          <div className="space-y-3">
            <div className="text-[16px] font-bold font-mono tracking-wider" style={{ color: "var(--accent-purple)" }}>ELIAS ONLINE</div>
            <div className="text-[14px] font-medium leading-relaxed max-w-md" style={{ color: "var(--text-secondary)" }}>
              No high-probability opportunity exists at the moment.
            </div>
            <div className="text-[12px] font-mono" style={{ color: "var(--text-disabled)" }}>
              ELIAS is monitoring the market.
            </div>
          </div>
        </div>
      </div>
    );
  }

  const regLabel = REGIME_LABELS[data.market_regime] ?? data.market_regime;
  const regColor = REGIME_COLORS[data.market_regime] ?? "#64748B";
  const brief = buildBriefing(data);
  const actionPlan: string[] = [];
  if (data.decision === "BUY" || data.decision === "SELL") {
    const side = data.decision === "BUY" ? "LONG" : "SHORT";
    if (data.entry > 0) actionPlan.push(`Open ${side} at ${formatUSD(data.entry)}`);
    if (data.tp > 0) actionPlan.push(`Take-profit at ${formatUSD(data.tp)}`);
    if (data.sl > 0) actionPlan.push(`Stop-loss at ${formatUSD(data.sl)}`);
    if (data.rr > 0) actionPlan.push(`Risk-to-reward ${data.rr.toFixed(2)}:1`);
  } else {
    actionPlan.push("No action recommended");
    actionPlan.push("Monitor for confirmation");
  }

  return (
    <div
      className="w-full rounded-[20px] overflow-hidden hero-enter"
      style={{
        background: `linear-gradient(135deg, #101827 0%, #0C1422 100%)`,
        border: "1px solid #243244",
        boxShadow: `0 8px 32px rgba(0,0,0,0.3), 0 0 60px ${style.glow}`,
        minHeight: 420,
      }}
    >
      <div className="h-[3px] w-full" style={{ background: `linear-gradient(to right, ${style.color}cc, transparent)` }} />

      {/* ===== BRIEFING ===== */}
      {true && (
        <div className="p-10 space-y-7" style={{ animation: "fadeIn 0.45s ease-out" }}>
          {/* Row 1: ELIAS identity */}
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <AIAvatar size={48} />
              <div className="flex items-baseline gap-3">
                <span className="text-[18px] font-bold font-mono tracking-wider" style={{ color: "var(--accent-purple)" }}>
                  ELIAS
                </span>
                <span
                  className="text-[9px] font-mono px-2.5 py-0.5 rounded-full"
                  style={{ background: "rgba(139,92,246,0.08)", color: "var(--accent-purple)", border: "1px solid rgba(139,92,246,0.2)" }}
                >
                  AI CHIEF INVESTMENT OFFICER
                </span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span
                className="text-[9px] font-mono font-medium px-2.5 py-0.5 rounded-lg"
                style={{ color: regColor, border: `1px solid ${regColor}44`, background: `${regColor}0d` }}
              >
                {regLabel}
              </span>
              <span className="text-[10px] font-mono" style={{ color: "var(--text-muted)" }}>{data.symbol}</span>
            </div>
          </div>

          {/* Row 2: Greeting */}
          <div>
            <p className="text-[17px] font-medium leading-relaxed" style={{ color: "var(--text-primary)" }}>
              {greeting()}, Commander.
            </p>
          </div>

          {/* Row 3: Decision — MASSIVE */}
          <div className="space-y-4">
            <div className="flex items-end gap-8">
              <div className="flex flex-col gap-1.5">
                <span className="text-[9px] font-semibold tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>DECISION</span>
                <span
                  className="text-[80px] font-extrabold font-mono tracking-tight leading-none"
                  style={{
                    color: style.color,
                    textShadow: `0 0 60px ${style.glow}, 0 0 120px ${style.glow}`,
                    lineHeight: 0.85,
                  }}
                >
                  {data.decision}
                </span>
              </div>
              <div className="flex flex-col gap-1.5 pb-2 flex-1 max-w-md">
                <span className="text-[9px] font-semibold tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>CONFIDENCE</span>
                <div className="flex items-center gap-4">
                  <span
                    className="text-[36px] font-bold font-mono tabular-nums"
                    style={{ color: style.color }}
                  >
                    {data.confidence.toFixed(1)}%
                  </span>
                  <div className="flex-1 h-[8px] rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${Math.min(data.confidence, 100)}%`,
                        background: `linear-gradient(to right, ${style.color}, ${style.color}99)`,
                        boxShadow: `0 0 14px ${style.glow}`,
                        animation: "progressFill 1.2s ease-out 0.3s both",
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Row 4: CIO Briefing */}
          {brief.length > 0 && (
            <div className="space-y-1.5 max-w-2xl">
              {brief.map((line, i) => (
                <p
                  key={i}
                  className="text-[13px] font-mono leading-relaxed"
                  style={{ color: "var(--text-secondary)", animation: `fadeSlideUp 0.35s ease-out ${0.2 + i * 0.08}s both` }}
                >
                  {line}
                </p>
              ))}
            </div>
          )}

          {/* Row 5: Action plan */}
          {actionPlan.length > 0 && (
            <div className="space-y-2.5">
              <span className="text-[9px] font-semibold tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>ACTION PLAN</span>
              <div className="flex flex-wrap gap-x-8 gap-y-2">
                {actionPlan.map((step, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2.5 text-[13px] font-mono"
                    style={{ color: "var(--text-secondary)", animation: `fadeSlideUp 0.3s ease-out ${0.35 + i * 0.06}s both` }}
                  >
                    <span className="w-[6px] h-[6px] rounded-full shrink-0" style={{ background: style.color, boxShadow: `0 0 6px ${style.glow}` }} />
                    {step}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Row 6: Technical grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 pt-1" style={{ animation: "fadeUp 0.4s ease-out 0.5s both" }}>
            <Cell label="Entry" value={formatUSD(data.entry)} />
            <Cell label="Take profit" value={formatUSD(data.tp)} color="#22C55E" />
            <Cell label="Stop loss" value={formatUSD(data.sl)} color="#EF4444" />
            <Cell label="Risk / reward" value={isNaN(data.rr) ? "—" : `${data.rr.toFixed(2)}:1`} color={isNaN(data.rr) ? "#64748B" : data.rr >= 2 ? "#22C55E" : data.rr >= 1 ? "#FACC15" : "#EF4444"} />
            <Cell label="Risk level" value={data.risk <= 0.3 ? "LOW" : data.risk <= 0.7 ? "MODERATE" : "HIGH"} color={data.risk <= 0.3 ? "#22C55E" : data.risk <= 0.7 ? "#FACC15" : "#EF4444"} />
            <Cell label="Market regime" value={regLabel} color={regColor} />
            <Cell label="Current position" value={data.decision === "WAIT" || data.decision === "HOLD" ? "NONE" : data.decision} color={data.decision === "WAIT" || data.decision === "HOLD" ? "#64748B" : style.color} />
          </div>

          {/* Row 7: Reasons + Warnings */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 pt-1" style={{ animation: "fadeUp 0.4s ease-out 0.6s both" }}>
            {data.reasons.length > 0 && (
              <div className="space-y-2.5">
                <span className="text-[9px] font-semibold tracking-[0.1em]" style={{ color: "var(--text-muted)" }}>KEY REASONS</span>
                <div className="space-y-1.5">
                  {data.reasons.map((r, i) => (
                    <div key={i} className="flex items-start gap-2.5 text-[12px] font-mono leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                      <span className="shrink-0 mt-0.5" style={{ color: style.color }}>→</span>
                      {r}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {(data.warnings.length > 0 || data.risk_notes.length > 0) && (
              <div className="space-y-2.5">
                <span className="text-[9px] font-semibold tracking-[0.1em]" style={{ color: "var(--accent-orange)" }}>INVALIDATION</span>
                <div className="space-y-1.5">
                  {data.warnings.map((w, i) => (
                    <div key={i} className="flex items-start gap-2.5 text-[12px] font-mono leading-relaxed" style={{ color: "var(--accent-yellow)" }}>
                      <span className="shrink-0 mt-0.5" style={{ color: "var(--accent-orange)" }}>⚠</span>
                      {w}
                    </div>
                  ))}
                  {data.risk_notes.map((r, i) => (
                    <div key={`risk-${i}`} className="flex items-start gap-2.5 text-[12px] font-mono leading-relaxed" style={{ color: "var(--text-muted)" }}>
                      <span className="shrink-0 mt-0.5 opacity-50">•</span>
                      {r}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between pt-2" style={{ borderTop: "1px solid #243244", animation: "fadeUp 0.4s ease-out 0.7s both" }}>
            <span className="text-[9px] font-mono" style={{ color: "var(--text-disabled)" }}>
              Last updated {data.timestamp ? new Date(data.timestamp).toLocaleTimeString() : "--"}
            </span>
            {data.supporting_signals.length > 0 && (
              <span className="text-[9px] font-mono" style={{ color: "var(--text-disabled)" }}>
                {data.supporting_signals.length} signal{data.supporting_signals.length > 1 ? "s" : ""}
              </span>
            )}
            {data.signal_id > 0 && (
              <span className="text-[9px] font-mono" style={{ color: "var(--text-disabled)" }}>
                #{data.signal_id}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
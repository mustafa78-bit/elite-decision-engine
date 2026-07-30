import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "../api/client";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import { addGlobalToast } from "../components/layout/toast-provider";

interface InstinctState {
  symbol: string;
  timeframe: string;
  disposition_vector: {
    courage: number;
    defensiveness: number;
    conviction: number;
    adaptability: number;
  };
  win_rate: number;
  profit_factor: number;
  total_trades: number;
  avg_pnl: number;
  vibe_score: number;
}

interface SufficiencyStatus {
  is_sufficient: boolean;
  sufficiency_ratio: number;
  total_events: number;
  duration_hours: number;
  regimes_encountered: string[];
  missing_reasons: string[];
}

interface SubstrateEntry {
  id: number;
  timestamp: string;
  symbol: string;
  timeframe: string;
  state_snapshot: any;
  action_taken: string;
  outcome: number | null;
  realized_at: string | null;
}

interface GraduationRecommendation {
  status: string;
  graduated: boolean;
  recommended_at: string | null;
  graduated_at: string | null;
  recommendation_payload: any;
  governance_rules: any;
}

export default function ExperienceEngine() {
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [timeframe, setTimeframe] = useState("1h");

  // Loaded states
  const [instinct, setInstinct] = useState<InstinctState | null>(null);
  const [sufficiency, setSufficiency] = useState<SufficiencyStatus | null>(null);
  const [substrates, setSubstrates] = useState<SubstrateEntry[]>([]);
  const [graduation, setGraduation] = useState<GraduationRecommendation | null>(null);

  const [loading, setLoading] = useState(true);

  // Controlled test produce states
  const [testAction, setActionTaken] = useState("LONG");
  const [testOutcome, setOutcome] = useState("0.15");
  const [testRegime, setRegime] = useState("TREND");

  // Load Policies
  const [policyMinEvents, setPolicyMinEvents] = useState(5);
  const [policyMinHours, setPolicyMinHours] = useState(24);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // 1. Distilled Instinct
      const instData = await apiFetch(`/experience/instinct?symbol=${symbol}&timeframe=${timeframe}`);
      setInstinct(instData);

      // 2. Sufficiency
      const suffData = await apiFetch(`/experience/sufficiency?symbol=${symbol}&timeframe=${timeframe}`);
      setSufficiency(suffData);

      // 3. Substrates
      const subsData = await apiFetch(`/experience/substrate?symbol=${symbol}&timeframe=${timeframe}`);
      setSubstrates(subsData);

      // 4. Graduation & Governance Recommendation
      const gradData = await apiFetch(`/experience/graduation/recommendation?symbol=${symbol}&timeframe=${timeframe}`);
      setGraduation(gradData);

    } catch (err) {
      console.error("Failed to load Experience Engine state:", err);
      addGlobalToast("Failed to sync chronological Experience Engine state", "error");
    } finally {
      setLoading(false);
    }
  }, [symbol, timeframe]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Governance explicit approval
  async function handleApprove() {
    try {
      await apiFetch("/experience/governance/approve", {
        method: "POST",
        body: JSON.stringify({
          symbol,
          timeframe,
          governor_name: "FOUNDER_GOVERNOR",
        }),
      });
      addGlobalToast("Governance APPROVAL granted: Environment Graduated", "success");
      loadData();
    } catch {
      addGlobalToast("Failed to grant Governance approval", "error");
    }
  }

  // Governance explicit rejection/revocation
  async function handleReject() {
    try {
      await apiFetch("/experience/governance/reject", {
        method: "POST",
        body: JSON.stringify({
          symbol,
          timeframe,
          governor_name: "FOUNDER_GOVERNOR",
        }),
      });
      addGlobalToast("Governance REVOCATION applied: Active constraints restored", "success");
      loadData();
    } catch {
      addGlobalToast("Failed to submit Governance decision", "error");
    }
  }

  // Governance policy dynamic adjustment
  async function handleUpdatePolicy() {
    try {
      await apiFetch("/experience/governance/policy", {
        method: "POST",
        body: JSON.stringify({
          min_events: policyMinEvents,
          min_hours: policyMinHours,
        }),
      });
      addGlobalToast("Governance Policy updated successfully", "success");
      loadData();
    } catch {
      addGlobalToast("Failed to update policy thresholds", "error");
    }
  }

  // Controlled simulation: producing raw walk-forward experience
  async function handleProduceTest() {
    try {
      const nowStr = new Date().toISOString();
      const realizedStr = new Date(Date.now() + 60000).toISOString(); // Realized 1 min later
      await apiFetch("/experience/test-produce", {
        method: "POST",
        body: JSON.stringify({
          timestamp: nowStr,
          symbol,
          timeframe,
          state_snapshot: {
            trend_score: 0.8,
            volume_score: 0.7,
            rsi: 65,
            regime: testRegime,
          },
          action_taken: testAction,
          outcome: parseFloat(testOutcome),
          realized_at: realizedStr,
        }),
      });
      addGlobalToast("Chronological experience generated in walk-forward substrate", "success");
      loadData();
    } catch (err: any) {
      addGlobalToast("Shield Active: Experience Simulator is inactive in Production environments", "error");
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto text-slate-100">
      {/* HEADER SECTION */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-purple-900/40 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-violet-400 via-pink-400 to-indigo-400">
            NEXUS Experience Engine
          </h1>
          <p className="text-slate-400 mt-1 text-sm">
            Visualizing chronological walk-forward living, instinct evolution, and governance boundaries.
          </p>
        </div>

        {/* CONTROLS */}
        <div className="flex items-center space-x-3 mt-4 md:mt-0 bg-slate-900/60 p-2 rounded-xl border border-slate-800">
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-slate-200 rounded px-3 py-1.5 text-xs focus:ring-2 focus:ring-violet-500"
          >
            <option value="BTCUSDT">BTCUSDT</option>
            <option value="ETHUSDT">ETHUSDT</option>
            <option value="SOLUSDT">SOLUSDT</option>
          </select>
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-slate-200 rounded px-3 py-1.5 text-xs focus:ring-2 focus:ring-violet-500"
          >
            <option value="15m">15m</option>
            <option value="1h">1h</option>
            <option value="4h">4h</option>
          </select>
          <Button onClick={loadData} className="bg-purple-950/40 border border-purple-800 text-xs py-1 px-3">
            Sync
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton className="h-96 w-full rounded-2xl" />
          <Skeleton className="h-96 w-full rounded-2xl" />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* COLUMN 1: DISTILLED INSTINCT DISPOSITION */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="bg-slate-950/70 border border-violet-900/30 shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-violet-600/10 rounded-full blur-3xl pointer-events-none" />
              <CardHeader className="border-b border-slate-900 pb-3">
                <CardTitle className="text-lg font-bold text-violet-300 flex items-center space-x-2">
                  <span className="text-xl">◆</span>
                  <span>Distilled Instinct Disposition</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6 space-y-6">

                {/* DISPOSITION VECTOR */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {instinct?.disposition_vector ? (
                    Object.entries(instinct.disposition_vector).map(([key, val]) => (
                      <div key={key} className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 text-center relative">
                        <div className="text-xs uppercase text-slate-500 font-semibold tracking-wider">{key}</div>
                        <div className="text-2xl font-black mt-2 text-violet-400">
                          {Math.round(val * 100)}%
                        </div>
                        <div className="w-full bg-slate-950 h-1.5 rounded-full mt-3 overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-violet-500 to-pink-500 h-full rounded-full transition-all duration-500"
                            style={{ width: `${val * 100}%` }}
                          />
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-slate-500 col-span-4 text-center">No Instinct Distilled</div>
                  )}
                </div>

                {/* AUXILIARY STATISTICS CONTRIBUTING TO INSTINCT */}
                <div className="bg-slate-900/30 p-4 rounded-xl border border-slate-800/80">
                  <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-3">Auxiliary Experience Metrics</div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                    <div>
                      <div className="text-xs text-slate-500">Win Rate</div>
                      <div className="text-lg font-bold text-slate-200 mt-1">
                        {instinct ? `${(instinct.win_rate * 100).toFixed(1)}%` : "0%"}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500">Profit Factor</div>
                      <div className="text-lg font-bold text-slate-200 mt-1">
                        {instinct ? instinct.profit_factor.toFixed(2) : "1.00"}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500">Total Lived Trades</div>
                      <div className="text-lg font-bold text-slate-200 mt-1">
                        {instinct ? instinct.total_trades : 0}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-500">Lived Vibe Index</div>
                      <div className="text-lg font-bold text-slate-200 mt-1">
                        {instinct ? instinct.vibe_score.toFixed(2) : "0.00"}
                      </div>
                    </div>
                  </div>
                </div>

                {/* EVOLUTION VIBE SUMMARY */}
                <div className="border-t border-slate-900 pt-4 flex items-center justify-between">
                  <span className="text-xs text-slate-400">Current instinctual state state phase:</span>
                  <Badge className="bg-pink-950/60 text-pink-300 border border-pink-800">
                    {instinct && instinct.total_trades > 0
                      ? instinct.vibe_score > 0.3
                        ? "HIGH_CONVICTION_STREAK"
                        : instinct.vibe_score < -0.3
                        ? "DEFENSIVE_SENSORY_SHIELD"
                        : "STABLE_ADAPTING"
                      : "AWAITING_CHRONOLOGICAL_START"}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* CHRONOLOGICAL LIVED TIMELINE (SUBSTRATES) */}
            <Card className="bg-slate-950/70 border border-slate-900">
              <CardHeader className="border-b border-slate-900 pb-3">
                <CardTitle className="text-lg font-bold text-indigo-300 flex items-center space-x-2">
                  <span className="text-xl">◆</span>
                  <span>Chronological Lived Timeline</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                {substrates.length === 0 ? (
                  <div className="text-center py-10 text-slate-500 text-sm">
                    No lived experiences recorded. Simulate experiences using the testing utility panel.
                  </div>
                ) : (
                  <div className="relative pl-6 border-l border-slate-800 space-y-6">
                    {substrates.map((sub, idx) => (
                      <div key={sub.id} className="relative">
                        {/* Glowing point */}
                        <div className={`absolute -left-[30px] top-1.5 w-4 h-4 rounded-full border-2 bg-slate-950 ${sub.outcome && sub.outcome > 0 ? "border-green-500 shadow-[0_0_8px_#22c55e]" : "border-red-500 shadow-[0_0_8px_#ef4444]"}`} />

                        <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center">
                          <div>
                            <div className="flex items-center space-x-2">
                              <span className="text-xs text-slate-500 font-mono">
                                {new Date(sub.timestamp).toLocaleTimeString()}
                              </span>
                              <Badge className="bg-indigo-950/40 text-indigo-300 border border-indigo-900 text-[10px]">
                                {sub.action_taken}
                              </Badge>
                              <span className="text-xs text-slate-300 font-medium">
                                Outcome PnL: {sub.outcome ? `${sub.outcome > 0 ? "+" : ""}${sub.outcome}` : "PENDING"}
                              </span>
                            </div>
                            <div className="text-xs text-slate-400 mt-2">
                              Regime: <span className="text-indigo-400">{sub.state_snapshot.regime || "UNKNOWN"}</span> | RSI: {sub.state_snapshot.rsi} | Trend: {sub.state_snapshot.trend_score}
                            </div>
                          </div>
                          <span className="text-[10px] text-slate-500 font-mono mt-2 md:mt-0">
                            ID: #{sub.id}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* COLUMN 2: SUFFICIENCY & GOVERNANCE */}
          <div className="space-y-6">

            {/* SUFFICIENCY CARD */}
            <Card className="bg-slate-950/70 border border-slate-900">
              <CardHeader className="border-b border-slate-900 pb-3">
                <CardTitle className="text-lg font-bold text-emerald-300 flex items-center space-x-2">
                  <span className="text-xl">◆</span>
                  <span>Experience Sufficiency</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6 space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-400">Status:</span>
                  <Badge className={sufficiency?.is_sufficient ? "bg-emerald-950 text-emerald-300 border border-emerald-800" : "bg-yellow-950 text-yellow-300 border border-yellow-800"}>
                    {sufficiency?.is_sufficient ? "SUFFICIENT" : "INSUFFICIENT"}
                  </Badge>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-xs text-slate-400">
                    <span>Sufficiency Ratio</span>
                    <span>{sufficiency ? Math.round(sufficiency.sufficiency_ratio * 100) : 0}%</span>
                  </div>
                  <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                      style={{ width: `${(sufficiency?.sufficiency_ratio || 0) * 100}%` }}
                    />
                  </div>
                </div>

                <div className="text-xs space-y-2 border-t border-slate-900 pt-3">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Total events encountered:</span>
                    <span className="font-mono text-slate-300">{sufficiency?.total_events || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Chronological exposure:</span>
                    <span className="font-mono text-slate-300">
                      {sufficiency ? sufficiency.duration_hours.toFixed(1) : 0} hours
                    </span>
                  </div>
                </div>

                {sufficiency?.missing_reasons && sufficiency.missing_reasons.length > 0 && (
                  <div className="bg-yellow-950/20 p-3 rounded-lg border border-yellow-900/40 mt-3 text-xs text-yellow-400">
                    <div className="font-semibold mb-1">Awaiting chronological milestones:</div>
                    <ul className="list-disc list-inside space-y-1 text-slate-400 text-[11px]">
                      {sufficiency.missing_reasons.map((r, i) => <li key={i}>{r}</li>)}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* GOVERNANCE & GRADUATION CARD */}
            <Card className="bg-slate-950/70 border border-violet-900/30 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-16 h-16 bg-pink-500/10 rounded-full blur-3xl pointer-events-none" />
              <CardHeader className="border-b border-slate-900 pb-3">
                <CardTitle className="text-lg font-bold text-pink-300 flex items-center space-x-2">
                  <span className="text-xl">◆</span>
                  <span>Governance & Graduation</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6 space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-400">Graduation Level:</span>
                  <Badge className="bg-pink-950 text-pink-300 border border-pink-800">
                    {graduation?.status || "PENDING"}
                  </Badge>
                </div>

                <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 text-xs text-slate-400 space-y-3">
                  <div className="font-semibold text-slate-300 border-b border-slate-800 pb-2">Active Multipliers:</div>
                  <div className="flex justify-between">
                    <span>Position Size Multiplier:</span>
                    <span className="font-mono text-pink-400 font-bold">
                      {graduation?.governance_rules.position_size_multiplier || "1.00"}x
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Risk Limit Multiplier:</span>
                    <span className="font-mono text-pink-400 font-bold">
                      {graduation?.governance_rules.risk_limit_multiplier || "1.00"}x
                    </span>
                  </div>
                </div>

                {/* ACTIVE GOVERNANCE ACTION BUTTONS */}
                <div className="pt-3 border-t border-slate-900 space-y-2">
                  <Button
                    onClick={handleApprove}
                    disabled={graduation?.status === "APPROVED_BY_GOVERNANCE"}
                    className="w-full bg-gradient-to-r from-violet-600 to-pink-600 hover:from-violet-500 hover:to-pink-500 text-white font-bold text-xs py-2 rounded-lg disabled:opacity-40"
                  >
                    Grant Governance Approval
                  </Button>
                  <Button
                    onClick={handleReject}
                    disabled={graduation?.status === "PENDING" || graduation?.status === "REJECTED_BY_GOVERNANCE"}
                    className="w-full bg-slate-900 hover:bg-slate-800 text-slate-400 border border-slate-800 font-bold text-xs py-2 rounded-lg disabled:opacity-40"
                  >
                    Revoke / Throttle Graduation
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* GOVERNANCE POLICY THRESHOLDS ADJUSTMENT */}
            <Card className="bg-slate-950/70 border border-slate-900">
              <CardHeader className="border-b border-slate-900 pb-2">
                <CardTitle className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                  Governance Policy Editor
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-3">
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <label className="text-slate-500 block mb-1">Min Events</label>
                    <input
                      type="number"
                      value={policyMinEvents}
                      onChange={(e) => setPolicyMinEvents(parseInt(e.target.value) || 0)}
                      className="bg-slate-950 border border-slate-800 text-slate-300 rounded p-1 w-full text-center font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-slate-500 block mb-1">Min Hours</label>
                    <input
                      type="number"
                      value={policyMinHours}
                      onChange={(e) => setPolicyMinHours(parseFloat(e.target.value) || 0)}
                      className="bg-slate-950 border border-slate-800 text-slate-300 rounded p-1 w-full text-center font-mono"
                    />
                  </div>
                </div>
                <Button
                  onClick={handleUpdatePolicy}
                  className="w-full bg-purple-950/50 hover:bg-purple-900/50 text-purple-300 border border-purple-800 text-xs py-1"
                >
                  Apply Threshold Policies
                </Button>
              </CardContent>
            </Card>

            {/* CONTROLLED TESTING UTILITY */}
            <Card className="bg-slate-950/70 border border-slate-900">
              <CardHeader className="border-b border-slate-900 pb-3">
                <CardTitle className="text-xs font-bold text-slate-400 uppercase tracking-widest flex justify-between items-center">
                  <span>Experience Simulator</span>
                  <Badge className="bg-blue-950 text-blue-300 border border-blue-900 text-[9px]">
                    DEV ONLY
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-3">
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <label className="text-slate-500 block mb-1">Simulated Action</label>
                    <select
                      value={testAction}
                      onChange={(e) => setActionTaken(e.target.value)}
                      className="bg-slate-950 border border-slate-800 text-slate-300 rounded p-1 w-full"
                    >
                      <option value="LONG">LONG</option>
                      <option value="SHORT">SHORT</option>
                      <option value="REJECT">REJECT</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-slate-500 block mb-1">PnL Outcome</label>
                    <input
                      type="text"
                      value={testOutcome}
                      onChange={(e) => setOutcome(e.target.value)}
                      className="bg-slate-950 border border-slate-800 text-slate-300 rounded p-1 w-full font-mono text-center"
                    />
                  </div>
                </div>

                <div className="text-xs">
                  <label className="text-slate-500 block mb-1">Market Regime</label>
                  <select
                    value={testRegime}
                    onChange={(e) => setRegime(e.target.value)}
                    className="bg-slate-950 border border-slate-800 text-slate-300 rounded p-1 w-full"
                  >
                    <option value="TREND">TREND</option>
                    <option value="RANGING">RANGING</option>
                    <option value="HIGH_VOLATILITY">HIGH_VOLATILITY</option>
                  </select>
                </div>

                <Button
                  onClick={handleProduceTest}
                  className="w-full bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 text-xs py-1.5 mt-2 rounded"
                >
                  Produce Chronological Experience
                </Button>
              </CardContent>
            </Card>

          </div>
        </div>
      )}
    </div>
  );
}

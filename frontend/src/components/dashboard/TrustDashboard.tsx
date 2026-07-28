import React, { useEffect, useState } from "react"
import {
  fetchTrustSummary,
  fetchTrustHistory,
  fetchTrustCalibration,
  fetchTrustAdvisors,
  fetchTrustEvidence,
  type TrustSummary,
  type TrustHistoryItem,
  type CalibrationData,
  type AdvisorRating,
  type TrustEvidence,
} from "../../api/trust"
import { Badge } from "../ui/badge"
import { Button } from "../ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card"

export default function TrustDashboard() {
  const [summary, setSummary] = useState<TrustSummary | null>(null)
  const [history, setHistory] = useState<TrustHistoryItem[]>([])
  const [calibration, setCalibration] = useState<CalibrationData | null>(null)
  const [advisors, setAdvisors] = useState<AdvisorRating[]>([])
  const [selectedDecisionId, setSelectedDecisionId] = useState<string>("")
  const [evidenceDetails, setEvidenceDetails] = useState<TrustEvidence | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [sumRes, histRes, calibRes, advRes] = await Promise.all([
        fetchTrustSummary("GLOBAL"),
        fetchTrustHistory(15),
        fetchTrustCalibration(),
        fetchTrustAdvisors(),
      ])
      setSummary(sumRes)
      setHistory(histRes)
      setCalibration(calibRes)
      setAdvisors(advRes)

      if (histRes.length > 0) {
        setSelectedDecisionId(histRes[0].decision_id)
      }
    } catch (err: any) {
      console.error(err)
      setError("Failed to load Trust Engine metrics.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (selectedDecisionId) {
      fetchTrustEvidence(selectedDecisionId)
        .then((res) => setEvidenceDetails(res))
        .catch((err) => console.error("Failed to load evidence details", err))
    }
  }, [selectedDecisionId])

  if (loading) {
    return (
      <div className="space-y-4 p-4 animate-pulse">
        <div className="h-10 bg-[var(--bg-elevated)] rounded w-1/4" />
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-20 bg-[var(--bg-elevated)] rounded" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="h-64 bg-[var(--bg-elevated)] rounded" />
          <div className="h-64 bg-[var(--bg-elevated)] rounded" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 text-center">
        <p className="text-[var(--accent-red)] font-mono text-xs">{error}</p>
        <Button onClick={loadData} size="sm" className="mt-4">
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* KPI Header */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <Card className="bg-[var(--bg-surface)]">
          <CardHeader className="py-2.5">
            <CardTitle className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">
              Trust Score
            </CardTitle>
          </CardHeader>
          <CardContent className="py-2">
            <span className="text-xl font-bold font-mono text-[var(--accent-green)]">
              {summary?.trust_score ?? "--"}%
            </span>
          </CardContent>
        </Card>

        <Card className="bg-[var(--bg-surface)]">
          <CardHeader className="py-2.5">
            <CardTitle className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">
              Calibration ECE
            </CardTitle>
          </CardHeader>
          <CardContent className="py-2">
            <span className="text-xl font-bold font-mono text-[var(--accent-blue)]">
              {calibration?.ece ?? "--"}%
            </span>
          </CardContent>
        </Card>

        <Card className="bg-[var(--bg-surface)]">
          <CardHeader className="py-2.5">
            <CardTitle className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">
              Brier Score
            </CardTitle>
          </CardHeader>
          <CardContent className="py-2">
            <span className="text-xl font-bold font-mono text-[var(--accent-yellow)]">
              {calibration?.brier_score ?? "--"}
            </span>
          </CardContent>
        </Card>

        <Card className="bg-[var(--bg-surface)]">
          <CardHeader className="py-2.5">
            <CardTitle className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">
              Historical Accuracy
            </CardTitle>
          </CardHeader>
          <CardContent className="py-2">
            <span className="text-xl font-bold font-mono text-white">
              {summary?.accuracy ?? "--"}%
            </span>
          </CardContent>
        </Card>

        <Card className="bg-[var(--bg-surface)]">
          <CardHeader className="py-2.5">
            <CardTitle className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">
              Advisor Reliability
            </CardTitle>
          </CardHeader>
          <CardContent className="py-2">
            <span className="text-xl font-bold font-mono text-purple-400">
              {summary?.reliability ?? "--"}%
            </span>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Calibration plot + Advisors - 5 cols */}
        <div className="lg:col-span-5 space-y-4">
          <Card className="bg-[var(--bg-surface)]">
            <CardHeader>
              <CardTitle className="text-xs uppercase tracking-wider">Confidence Calibration Curve</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                {calibration?.points.map((p, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between text-[10px] font-mono">
                      <span className="text-[var(--text-muted)]">Bin ({(p.confidence_bin * 100).toFixed(0)}% Conf)</span>
                      <span className="text-white">Actual Accuracy: {p.actual_accuracy}% ({p.prediction_count} trials)</span>
                    </div>
                    <div className="h-2 bg-[var(--bg-deep)] rounded-full overflow-hidden flex">
                      <div
                        className="h-full bg-[var(--accent-blue)] rounded-l-full"
                        style={{ width: `${p.confidence_bin * 100}%`, opacity: 0.4 }}
                      />
                      <div
                        className="h-full bg-[var(--accent-green)] rounded-r-full -ml-[100%] z-10"
                        style={{ width: `${p.actual_accuracy}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Murphy decomposition */}
              <div className="pt-3 border-t border-[var(--border-subtle)] grid grid-cols-3 gap-2 text-center text-[10px] font-mono">
                <div>
                  <div className="text-[var(--text-muted)]">Reliability</div>
                  <div className="text-white mt-0.5">{calibration?.reliability ?? "0.0"}</div>
                </div>
                <div>
                  <div className="text-[var(--text-muted)]">Resolution</div>
                  <div className="text-white mt-0.5">{calibration?.resolution ?? "0.0"}</div>
                </div>
                <div>
                  <div className="text-[var(--text-muted)]">Uncertainty</div>
                  <div className="text-white mt-0.5">{calibration?.uncertainty ?? "0.0"}</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-[var(--bg-surface)]">
            <CardHeader>
              <CardTitle className="text-xs uppercase tracking-wider">AI Council Advisor Ratings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {advisors.map((adv) => (
                  <div key={adv.name} className="flex items-center justify-between py-1 border-b border-[var(--border-subtle)] last:border-0">
                    <div>
                      <div className="text-xs font-semibold text-white">{adv.name} Agent</div>
                      <div className="text-[10px] text-[var(--text-muted)]">Weight: {(adv.weight * 100).toFixed(0)}% | Consistency: {adv.consistency}%</div>
                    </div>
                    <div className="text-right">
                      <Badge variant={adv.reliability_score >= 80 ? "success" : "info"} className="text-[9px]">
                        {adv.reliability_score.toFixed(1)} Index
                      </Badge>
                      <div className="text-[10px] text-[var(--text-muted)] font-mono mt-0.5">Acc: {adv.accuracy}%</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Timeline & Replay Audit - 7 cols */}
        <div className="lg:col-span-7 space-y-4">
          <Card className="bg-[var(--bg-surface)]">
            <CardHeader>
              <CardTitle className="text-xs uppercase tracking-wider">Decision Provenance & Timeline</CardTitle>
            </CardHeader>
            <CardContent className="p-0 max-h-[350px] overflow-y-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[var(--bg-deep)] border-b border-[var(--border-subtle)] text-[10px] text-[var(--text-muted)] uppercase tracking-wider">
                  <tr>
                    <th className="p-2.5">Symbol</th>
                    <th className="p-2.5">Pred Direction</th>
                    <th className="p-2.5">Predicted Conf</th>
                    <th className="p-2.5">Actual Outcome</th>
                    <th className="p-2.5">Provenance Hash</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-subtle)]">
                  {history.map((h) => (
                    <tr
                      key={h.decision_id}
                      onClick={() => setSelectedDecisionId(h.decision_id)}
                      className={`cursor-pointer transition-colors hover:bg-[var(--bg-elevated)]/30 ${selectedDecisionId === h.decision_id ? "bg-[var(--bg-elevated)]/70" : ""}`}
                    >
                      <td className="p-2.5 text-white font-semibold">{h.symbol}</td>
                      <td className="p-2.5">
                        <Badge variant={h.predicted_direction === "LONG" ? "success" : "danger"} className="text-[9px]">
                          {h.predicted_direction}
                        </Badge>
                      </td>
                      <td className="p-2.5 text-white">{h.predicted_confidence}%</td>
                      <td className="p-2.5">
                        <Badge
                          variant={h.actual_outcome === "CORRECT" ? "success" : h.actual_outcome === "INCORRECT" ? "danger" : "default"}
                          className="text-[9px]"
                        >
                          {h.actual_outcome}
                        </Badge>
                      </td>
                      <td className="p-2.5 text-[10px] text-[var(--text-muted)]">{h.provenance_hash.slice(0, 10)}...</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>

          {/* Active Audit Evidence Panel */}
          {evidenceDetails && (
            <Card className="bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
              <CardHeader className="py-3 bg-[var(--bg-deep)]/40 flex flex-row items-center justify-between border-b border-[var(--border-subtle)]">
                <div>
                  <CardTitle className="text-xs uppercase tracking-wider">Provenance Replay Audit</CardTitle>
                  <p className="text-[10px] text-[var(--text-muted)] font-mono mt-0.5">ID: {evidenceDetails.decision_id}</p>
                </div>
                <Badge variant="success" className="text-[10px] font-mono">
                  Verified Replayable
                </Badge>
              </CardHeader>
              <CardContent className="p-4 space-y-4">
                {/* Why explanation */}
                <div>
                  <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider mb-1 font-semibold">Why was this decision approved?</div>
                  <ul className="list-disc pl-4 space-y-1">
                    {evidenceDetails.why.map((w, idx) => (
                      <li key={idx} className="text-xs text-white leading-relaxed">{w}</li>
                    ))}
                  </ul>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-[var(--border-subtle)]">
                  {/* Indicators */}
                  <div>
                    <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider mb-1 font-semibold">Which Indicators?</div>
                    {evidenceDetails.indicators.length === 0 ? (
                      <span className="text-[10px] text-[var(--text-muted)] font-mono">No indicator alerts.</span>
                    ) : (
                      <div className="space-y-1.5">
                        {evidenceDetails.indicators.slice(0, 3).map((ind, idx) => (
                          <div key={idx} className="text-xs text-white font-mono flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 bg-blue-400 rounded-full shrink-0" />
                            {ind.title || ind}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Whales */}
                  <div>
                    <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider mb-1 font-semibold">Which Whales?</div>
                    {evidenceDetails.whales.length === 0 ? (
                      <span className="text-[10px] text-[var(--text-muted)] font-mono">No whale alerts.</span>
                    ) : (
                      <div className="space-y-1.5">
                        {evidenceDetails.whales.slice(0, 3).map((w, idx) => (
                          <div key={idx} className="text-xs text-white font-mono flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 bg-green-400 rounded-full shrink-0" />
                            {w.title || w}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-[var(--border-subtle)]">
                  {/* News */}
                  <div>
                    <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider mb-1 font-semibold">Which News?</div>
                    {evidenceDetails.news.length === 0 ? (
                      <span className="text-[10px] text-[var(--text-muted)] font-mono">No major news events.</span>
                    ) : (
                      <div className="space-y-1.5">
                        {evidenceDetails.news.slice(0, 3).map((n, idx) => (
                          <div key={idx} className="text-xs text-white font-mono flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 bg-orange-400 rounded-full shrink-0" />
                            {n.title || n}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Events */}
                  <div>
                    <div className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider mb-1 font-semibold">Which Pipeline Events?</div>
                    {evidenceDetails.events.length === 0 ? (
                      <span className="text-[10px] text-[var(--text-muted)] font-mono">No matching system pipeline events.</span>
                    ) : (
                      <div className="space-y-1.5">
                        {evidenceDetails.events.slice(0, 3).map((e, idx) => (
                          <div key={idx} className="text-xs text-white font-mono flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 bg-purple-400 rounded-full shrink-0" />
                            {e.title || e}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

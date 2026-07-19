from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from decision.evidence.dto import EvidenceItem
from decision.evidence.evidence_registry import get_category
from decision.evidence.source_trace import SourceTrace


def parse_decision_result(result: Any, symbol: str = "") -> list[EvidenceItem]:
    items: list[EvidenceItem] = []

    decision = getattr(result, "decision", "UNKNOWN") or "UNKNOWN"
    confidence = getattr(result, "confidence", 0.0) or 0.0
    score = getattr(result, "score", 0.0) or 0.0
    risk_score = getattr(result, "risk_score", 0.0) or 0.0
    reasons = getattr(result, "reasons", []) or []
    warnings = getattr(result, "warnings", []) or []

    cat = get_category("decision_quality")

    items.append(
        EvidenceItem(
            title=f"Decision: {decision}",
            description=f"Score {score:.1f}, Risk {risk_score:.2f}",
            engine="decision",
            category="decision_quality",
            severity="HIGH" if confidence >= 70 else "MEDIUM",
            confidence=confidence / 100.0 if confidence > 1.0 else confidence,
            supports_decision=True,
            source=SourceTrace(origin=f"decision/{symbol}" if symbol else "decision", engine="decision"),
        )
    )

    for r in reasons:
        items.append(
            EvidenceItem(
                title="Reason",
                description=str(r),
                engine="decision",
                category="decision_quality",
                severity="LOW",
                confidence=0.7,
                supports_decision=True,
                source=SourceTrace(origin=f"decision/{symbol}" if symbol else "decision", engine="decision"),
            )
        )

    for w in warnings:
        items.append(
            EvidenceItem(
                title="Warning",
                description=str(w),
                engine="decision",
                category="decision_quality",
                severity="MEDIUM",
                confidence=0.8,
                supports_decision=False,
                source=SourceTrace(origin=f"decision/{symbol}" if symbol else "decision", engine="decision"),
            )
        )

    return items


def parse_risk_decision(result: Any, symbol: str = "") -> list[EvidenceItem]:
    items: list[EvidenceItem] = []

    allowed = getattr(result, "allowed", True)
    reason = getattr(result, "reason", "")

    if not allowed:
        items.append(
            EvidenceItem(
                title="Trade Rejected by Risk",
                description=reason or "Risk engine blocked the trade",
                engine="risk_engine",
                category="risk_rejection",
                severity="CRITICAL",
                confidence=0.95,
                supports_decision=False,
                source=SourceTrace(origin=symbol or "unknown", engine="risk_engine"),
            )
        )

    checks = getattr(result, "checks", ())
    if isinstance(checks, dict):
        for check_name, check_value in checks.items():
            severity = "HIGH"
            desc = f"{check_name}: {check_value}"
            items.append(
                EvidenceItem(
                    title=f"Risk Check: {check_name}",
                    description=desc,
                    engine="risk_engine",
                    category="risk_volatility",
                    severity=severity,
                    confidence=0.85,
                    supports_decision=False,
                    source=SourceTrace(origin=symbol or "unknown", engine="risk_engine"),
                )
            )
    elif isinstance(checks, (list, tuple)):
        for c in checks:
            name = getattr(c, "name", "check")
            passed = getattr(c, "passed", True)
            detail = getattr(c, "detail", "")
            items.append(
                EvidenceItem(
                    title=f"Risk: {name}",
                    description=detail or f"{'Passed' if passed else 'Failed'}",
                    engine="risk_engine",
                    category="risk_volatility",
                    severity="LOW" if passed else "HIGH",
                    confidence=0.85,
                    supports_decision=passed,
                    source=SourceTrace(origin=symbol or "unknown", engine="risk_engine"),
                )
            )

    return items


def parse_scanner_opportunity(result: Any) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []

    symbol = getattr(result, "symbol", "UNKNOWN")
    side = getattr(result, "side", "LONG")
    score = getattr(result, "score", 0.0)
    confidence = getattr(result, "confidence", 0.0)
    strategy = getattr(result, "strategy", "unknown")
    reason = getattr(result, "reason", "")

    category_key = f"scanner_{strategy.lower()}"
    cat = get_category(category_key)

    items.append(
        EvidenceItem(
            title=f"{strategy} on {symbol}",
            description=reason or f"{strategy} signal detected for {symbol} ({side})",
            engine="scanner",
            category=cat.name,
            severity=cat.severity,
            confidence=confidence / 100.0 if confidence > 1.0 else confidence,
            supports_decision=True,
            source=SourceTrace(origin=symbol, engine="scanner"),
        )
    )

    signals = getattr(result, "signals", [])
    for s in signals[:5]:
        items.append(
            EvidenceItem(
                title="Signal",
                description=str(s),
                engine="scanner",
                category=cat.name,
                severity="LOW",
                confidence=0.6,
                supports_decision=True,
                source=SourceTrace(origin=symbol, engine="scanner"),
            )
        )

    return items


def parse_council_report(result: Any) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []

    symbol = getattr(result, "symbol", "UNKNOWN") or "UNKNOWN"
    direction = getattr(result, "consensus_direction", "NEUTRAL") or "NEUTRAL"
    score = getattr(result, "consensus_score", 0.0) or 0.0
    agreement = getattr(result, "agreement_level", "none") or "none"
    agreeing = getattr(result, "sources_agreeing", 0) or 0
    disagreeing = getattr(result, "sources_disagreeing", 0) or 0

    items.append(
        EvidenceItem(
            title=f"Council: {direction} ({agreement})",
            description=f"{agreeing} for, {disagreeing} against — score {score:.1f}",
            engine="council",
            category="council_consensus",
            severity="HIGH" if agreement in ("strong", "moderate") else "MEDIUM",
            confidence=score / 100.0 if score > 1.0 else score,
            supports_decision=True,
            source=SourceTrace(origin=symbol, engine="council"),
        )
    )

    agent_reports = getattr(result, "agent_reports", [])
    for agent in agent_reports:
        agent_name = getattr(agent, "agent_name", "unknown")
        agent_dir = getattr(agent, "direction", "NEUTRAL")
        agent_conf = getattr(agent, "confidence", 0.0)
        agent_reasoning = getattr(agent, "reasoning", [])

        items.append(
            EvidenceItem(
                title=f"{agent_name}: {agent_dir}",
                description="; ".join(agent_reasoning[:3]) if agent_reasoning else f"{agent_name} votes {agent_dir}",
                engine="council",
                category="council_agent",
                severity="MEDIUM",
                confidence=agent_conf / 100.0 if agent_conf > 1.0 else agent_conf,
                supports_decision=True,
                source=SourceTrace(origin=symbol, engine="council"),
            )
        )

    return items


def parse_portfolio_summary(result: Any) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []

    exposure = getattr(result, "current_exposure", 0.0) or 0.0
    max_exposure = getattr(result, "max_exposure", 0.0) or 0.0
    open_pnl = getattr(result, "open_pnl", 0.0) or 0.0
    win_rate = getattr(result, "win_rate", 0.0) or 0.0

    if open_pnl < -1000:
        items.append(
            EvidenceItem(
                title="Portfolio Drawdown",
                description=f"Open PnL: ${open_pnl:.0f}",
                engine="portfolio",
                category="portfolio_exposure",
                severity="HIGH",
                confidence=0.9,
                supports_decision=False,
                source=SourceTrace(origin="global", engine="portfolio"),
            )
        )

    if max_exposure > 0 and exposure > max_exposure * 0.8:
        items.append(
            EvidenceItem(
                title="Near Exposure Limit",
                description=f"Exposure {exposure:.0f} / {max_exposure:.0f}",
                engine="portfolio",
                category="portfolio_exposure",
                severity="HIGH",
                confidence=0.85,
                supports_decision=False,
                source=SourceTrace(origin="global", engine="portfolio"),
            )
        )

    if win_rate > 0:
        supports = win_rate >= 50
        items.append(
            EvidenceItem(
                title="Historical Win Rate",
                description=f"{win_rate:.1f}%",
                engine="portfolio",
                category="portfolio_fit",
                severity="LOW",
                confidence=win_rate / 100.0,
                supports_decision=supports,
                source=SourceTrace(origin="global", engine="portfolio"),
            )
        )

    return items


def parse_market_regime(result: Any) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []

    if isinstance(result, dict):
        regime = result.get("regime", "UNKNOWN")
        trend = result.get("trend", "NEUTRAL")
        trend_strength = result.get("trend_strength", "UNKNOWN")
        volatility = result.get("volatility_class", "UNKNOWN")
        score = result.get("score", 0.0)
    else:
        regime = getattr(result, "regime", "UNKNOWN")
        trend = getattr(result, "trend", "NEUTRAL")
        trend_strength = getattr(result, "trend_strength", "UNKNOWN")
        volatility = getattr(result, "volatility_class", "UNKNOWN")
        score = getattr(result, "score", 0.0)

    bullish_trends = ("BULLISH", "RECOVERING")
    is_bullish = trend in bullish_trends

    items.append(
        EvidenceItem(
            title=f"Market: {regime} ({trend})",
            description=f"Trend {trend_strength}, Volatility {volatility}",
            engine="market_regime",
            category="market_regime",
            severity="HIGH" if volatility in ("EXTREME", "HIGH") else "MEDIUM",
            confidence=score,
            supports_decision=is_bullish,
            source=SourceTrace(origin="global", engine="market_regime"),
        )
    )

    if volatility in ("EXTREME", "HIGH"):
        items.append(
            EvidenceItem(
                title="Elevated Volatility",
                description=f"Volatility class: {volatility}",
                engine="market_regime",
                category="market_regime",
                severity="HIGH",
                confidence=0.85,
                supports_decision=False,
                source=SourceTrace(origin="global", engine="market_regime"),
            )
        )

    return items


def parse_whale_result(results: Any) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []

    whale_list = results if isinstance(results, list) else []

    for w in whale_list:
        symbol = w.get("symbol", "UNKNOWN")
        wtype = w.get("type", "WHALE_MOVE")
        severity = w.get("severity", "medium")
        description = w.get("description", "")
        confidence = w.get("confidence", 0.5)

        items.append(
            EvidenceItem(
                title=f"Whale: {wtype} on {symbol}",
                description=description or f"{wtype} detected for {symbol}",
                engine="whale",
                category="whale_activity",
                severity=severity.upper(),
                confidence=confidence,
                supports_decision=True,
                source=SourceTrace(origin=symbol, engine="whale"),
            )
        )

    return items


def parse_explain_result(result: Any) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []

    decision = getattr(result, "decision", "") or ""
    confidence = getattr(result, "confidence", 0.0) or 0.0
    reasons = getattr(result, "reasons", []) or []
    warnings = getattr(result, "warnings", []) or []
    supporting_signals = getattr(result, "supporting_signals", []) or []
    risk_notes = getattr(result, "risk_notes", []) or []
    summary = getattr(result, "summary", "") or ""

    if summary:
        items.append(
            EvidenceItem(
                title="Explanation Summary",
                description=summary,
                engine="explain",
                category="explain_signal",
                severity="MEDIUM",
                confidence=confidence / 100.0 if confidence > 1.0 else confidence,
                supports_decision=True,
                source=SourceTrace(origin="explain", engine="explain"),
            )
        )

    for r in reasons:
        items.append(
            EvidenceItem(
                title="Reason",
                description=str(r),
                engine="explain",
                category="explain_signal",
                severity="LOW",
                confidence=0.7,
                supports_decision=True,
                source=SourceTrace(origin="explain", engine="explain"),
            )
        )

    for w in warnings:
        items.append(
            EvidenceItem(
                title="Warning",
                description=str(w),
                engine="explain",
                category="explain_signal",
                severity="MEDIUM",
                confidence=0.8,
                supports_decision=False,
                source=SourceTrace(origin="explain", engine="explain"),
            )
        )

    for s in supporting_signals:
        items.append(
            EvidenceItem(
                title="Supporting Signal",
                description=str(s),
                engine="explain",
                category="explain_signal",
                severity="LOW",
                confidence=0.7,
                supports_decision=True,
                source=SourceTrace(origin="explain", engine="explain"),
            )
        )

    for n in risk_notes:
        items.append(
            EvidenceItem(
                title="Risk Note",
                description=str(n),
                engine="explain",
                category="explain_signal",
                severity="MEDIUM",
                confidence=0.8,
                supports_decision=False,
                source=SourceTrace(origin="explain", engine="explain"),
            )
        )

    return items

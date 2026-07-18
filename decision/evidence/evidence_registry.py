from __future__ import annotations

from dataclasses import dataclass, field


SEVERITY_ORDER = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


@dataclass(frozen=True)
class EvidenceCategory:
    name: str
    severity: str = "MEDIUM"
    priority: int = 3
    category: str = "general"
    color: str = "#6b7280"
    icon: str = "info"

    def to_dict(self) -> dict[str, str | int]:
        return {
            "name": self.name,
            "severity": self.severity,
            "priority": self.priority,
            "category": self.category,
            "color": self.color,
            "icon": self.icon,
        }


REGISTRY: dict[str, EvidenceCategory] = {
    "scanner_momentum": EvidenceCategory(
        name="Momentum Breakout",
        severity="HIGH",
        priority=1,
        category="scanner",
        color="#10b981",
        icon="trending-up",
    ),
    "scanner_trend": EvidenceCategory(
        name="Trend Signal",
        severity="HIGH",
        priority=1,
        category="scanner",
        color="#10b981",
        icon="trending-up",
    ),
    "scanner_reversal": EvidenceCategory(
        name="Reversal Signal",
        severity="MEDIUM",
        priority=2,
        category="scanner",
        color="#f59e0b",
        icon="refresh",
    ),
    "scanner_breakout": EvidenceCategory(
        name="Breakout Signal",
        severity="HIGH",
        priority=1,
        category="scanner",
        color="#10b981",
        icon=" maximize",
    ),
    "scanner_liquidity": EvidenceCategory(
        name="Liquidity Signal",
        severity="LOW",
        priority=3,
        category="scanner",
        color="#6b7280",
        icon="droplets",
    ),
    "council_consensus": EvidenceCategory(
        name="Council Consensus",
        severity="HIGH",
        priority=1,
        category="council",
        color="#8b5cf6",
        icon="users",
    ),
    "council_agent": EvidenceCategory(
        name="Agent Opinion",
        severity="MEDIUM",
        priority=2,
        category="council",
        color="#a78bfa",
        icon="user-check",
    ),
    "risk_volatility": EvidenceCategory(
        name="Volatility Risk",
        severity="HIGH",
        priority=1,
        category="risk",
        color="#ef4444",
        icon="alert-triangle",
    ),
    "risk_exposure": EvidenceCategory(
        name="Exposure Risk",
        severity="CRITICAL",
        priority=1,
        category="risk",
        color="#dc2626",
        icon="shield-off",
    ),
    "risk_rejection": EvidenceCategory(
        name="Trade Rejection",
        severity="CRITICAL",
        priority=1,
        category="risk",
        color="#dc2626",
        icon="ban",
    ),
    "portfolio_fit": EvidenceCategory(
        name="Portfolio Fit",
        severity="MEDIUM",
        priority=2,
        category="portfolio",
        color="#3b82f6",
        icon="briefcase",
    ),
    "portfolio_exposure": EvidenceCategory(
        name="Portfolio Exposure",
        severity="HIGH",
        priority=2,
        category="portfolio",
        color="#2563eb",
        icon="bar-chart",
    ),
    "market_regime": EvidenceCategory(
        name="Market Regime",
        severity="HIGH",
        priority=1,
        category="market",
        color="#06b6d4",
        icon="activity",
    ),
    "whale_activity": EvidenceCategory(
        name="Whale Activity",
        severity="MEDIUM",
        priority=2,
        category="whale",
        color="#f97316",
        icon="shark",
    ),
    "explain_signal": EvidenceCategory(
        name="Explanation Signal",
        severity="MEDIUM",
        priority=2,
        category="explain",
        color="#6366f1",
        icon="file-text",
    ),
    "decision_quality": EvidenceCategory(
        name="Decision Quality",
        severity="HIGH",
        priority=1,
        category="decision",
        color="#14b8a6",
        icon="check-circle",
    ),
}


def get_category(key: str) -> EvidenceCategory:
    return REGISTRY.get(key, EvidenceCategory(name=key, category="general"))

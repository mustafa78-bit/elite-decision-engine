from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MissionProfile:
    room_id: str
    display_name: str
    purpose: str
    tone: str
    priority: int
    allowed_context: list[str]
    allowed_tools: list[str]
    briefing_style: str

    future_voice: str = ""
    future_avatar: str = ""
    future_theme: str = ""

    def to_dict(self) -> dict:
        return {
            "room_id": self.room_id,
            "display_name": self.display_name,
            "purpose": self.purpose,
            "tone": self.tone,
            "priority": self.priority,
            "briefing_style": self.briefing_style,
        }


COMMAND_DECK = MissionProfile(
    room_id="command_deck",
    display_name="Command Deck",
    purpose="Central headquarters overview. Monitor portfolio, market regime, risk, and active missions.",
    tone="strategic",
    priority=1,
    allowed_context=["portfolio_summary", "market_regime", "risk_metrics", "council_latest"],
    allowed_tools=["greet", "briefing", "query"],
    briefing_style="executive_summary",
)

SCANNER = MissionProfile(
    room_id="scanner",
    display_name="Scanner Room",
    purpose="Review market scan results, signal strength, and technical opportunities.",
    tone="analytical",
    priority=2,
    allowed_context=["scanner_signals", "market_regime"],
    allowed_tools=["query"],
    briefing_style="technical",
)

WHALE = MissionProfile(
    room_id="whale",
    display_name="Whale Intelligence",
    purpose="Analyze whale movements, large transactions, and OI trends.",
    tone="analytical",
    priority=3,
    allowed_context=["whale_activity", "market_regime"],
    allowed_tools=["query"],
    briefing_style="data",
)

PORTFOLIO = MissionProfile(
    room_id="portfolio",
    display_name="Portfolio",
    purpose="Analyze portfolio health, PnL, exposure, and performance metrics.",
    tone="advisory",
    priority=2,
    allowed_context=[
        "portfolio_summary", "portfolio_distribution",
        "portfolio_performance", "portfolio_risk",
    ],
    allowed_tools=["query", "briefing"],
    briefing_style="financial",
)

RISK_OPERATIONS = MissionProfile(
    room_id="risk_operations",
    display_name="Risk Operations",
    purpose="Monitor risk metrics, exposure limits, VaR, and drawdown status.",
    tone="cautionary",
    priority=1,
    allowed_context=["risk_metrics", "portfolio_risk", "market_regime"],
    allowed_tools=["query", "briefing"],
    briefing_style="risk_report",
)

MISSION_ARCHIVE = MissionProfile(
    room_id="mission_archive",
    display_name="Mission Archive",
    purpose="Review past trades, historical performance, and completed missions.",
    tone="reflective",
    priority=5,
    allowed_context=["portfolio_summary", "portfolio_performance"],
    allowed_tools=["query"],
    briefing_style="historical",
)

COUNCIL_CHAMBER = MissionProfile(
    room_id="council_chamber",
    display_name="AI Council Chamber",
    purpose="Review AI council consensus, agent reports, and recommendation rankings.",
    tone="deliberative",
    priority=2,
    allowed_context=["council_full", "market_regime"],
    allowed_tools=["query", "briefing"],
    briefing_style="consensus",
)


PROFILES_BY_ROOM: dict[str, MissionProfile] = {
    p.room_id: p
    for p in [
        COMMAND_DECK,
        SCANNER,
        WHALE,
        PORTFOLIO,
        RISK_OPERATIONS,
        MISSION_ARCHIVE,
        COUNCIL_CHAMBER,
    ]
}


def get_profile(room_id: str) -> MissionProfile:
    return PROFILES_BY_ROOM.get(room_id, COMMAND_DECK)

from typing import Dict, Any

class FounderPlatformCoordinator:
    """
    Coordinates Founder preferences/dashboard and Platform subsystems telemetry.
    """
    def __init__(self):
        self.founder_preferences = {
            "risk_mode": "conservative",
            "preferred_leverage": 3,
            "max_drawdown_tolerance_pct": 5.0
        }

    def get_founder_preferences(self) -> Dict[str, Any]:
        return self.founder_preferences

    def update_founder_preference(self, key: str, value: Any) -> None:
        self.founder_preferences[key] = value

    def get_platform_telemetry(self) -> Dict[str, Any]:
        return {
            "market_intelligence_status": "ONLINE",
            "portfolio_health_index": 96.2,
            "risk_guards_active_rules": 5,
            "sentiment_trend": "bullish"
        }

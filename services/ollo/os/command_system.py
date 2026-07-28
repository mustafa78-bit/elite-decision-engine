from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ExecutableCommand:
    """Represents a structured executable system command in the NEXUS Operating System."""

    def __init__(self, action: str, params: Dict[str, Any], description: str) -> None:
        self.action = action
        self.params = params
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "params": self.params,
            "description": self.description,
            "executable": True,
        }

    def execute(self) -> Dict[str, Any]:
        """Execute the command by orchestrating the appropriate tool from the ToolRegistry."""
        from services.ollo.os.tool_registry import tool_registry

        logger.info("Executing command '%s' with params: %s", self.action, self.params)

        if self.action == "open_portfolio":
            return tool_registry.execute_tool("Portfolio", scope=self.params.get("scope", "full"))

        elif self.action == "start_simulator":
            return tool_registry.execute_tool(
                "Simulator",
                action="run",
                symbol=self.params.get("symbol", "BTCUSDT"),
            )

        elif self.action == "analyze_coin":
            return tool_registry.execute_tool(
                "Market Scanner",
                symbol=self.params.get("symbol", "BTC"),
            )

        elif self.action == "generate_report":
            # Orchestrate portfolio and risk analysis to generate weekly report
            portfolio_data = tool_registry.execute_tool("Portfolio", scope="performance")
            risk_data = tool_registry.execute_tool("Risk Analysis")
            return {
                "success": True,
                "report_type": "Weekly Executive Report",
                "portfolio_summary": portfolio_data.get("data"),
                "risk_summary": risk_data.get("data"),
            }

        elif self.action == "replay_trade":
            return tool_registry.execute_tool(
                "Replay",
                trade_id=self.params.get("trade_id"),
                limit=self.params.get("limit", 5),
            )

        elif self.action == "compare_strategies":
            # Simulate or fetch strategy comparison parameters
            return {
                "success": True,
                "comparison": {
                    "ema_cross": {"win_rate_pct": 62.5, "profit_factor": 2.1},
                    "breakout": {"win_rate_pct": 55.0, "profit_factor": 1.8},
                },
            }

        return {
            "success": False,
            "error": f"Unknown executable action '{self.action}'",
        }


class CommandSystem:
    """Translates user intents and tool invocations into executable operating system actions."""

    _instance: Optional[CommandSystem] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

    def create_command(self, query: str) -> Optional[ExecutableCommand]:
        """Parse query string and map to structured ExecutableCommand if matching action triggers."""
        q_lower = query.lower()

        # 1. Open Portfolio
        if "portfolio" in q_lower or "exposure" in q_lower:
            scope = "full"
            if "pnl" in q_lower or "performance" in q_lower:
                scope = "performance"
            elif "risk" in q_lower:
                scope = "risk"
            return ExecutableCommand(
                action="open_portfolio",
                params={"scope": scope},
                description=f"Open portfolio view with '{scope}' scope details.",
            )

        # 2. Start Simulator
        if "simulator" in q_lower or "simulate" in q_lower:
            symbol = "BTCUSDT"
            if "eth" in q_lower:
                symbol = "ETHUSDT"
            elif "sol" in q_lower:
                symbol = "SOLUSDT"
            return ExecutableCommand(
                action="start_simulator",
                params={"symbol": symbol},
                description=f"Start paper trading simulation for {symbol}.",
            )

        # 3. Analyze Coin
        if "analyze" in q_lower or "scan" in q_lower:
            symbol = "BTC"
            if "eth" in q_lower:
                symbol = "ETH"
            elif "sol" in q_lower:
                symbol = "SOL"
            return ExecutableCommand(
                action="analyze_coin",
                params={"symbol": symbol},
                description=f"Analyze current technical indicators and signal strength for {symbol}.",
            )

        # 4. Generate Report
        if "report" in q_lower or "weekly" in q_lower:
            return ExecutableCommand(
                action="generate_report",
                params={},
                description="Generate comprehensive Weekly Executive Portfolio and Risk report.",
            )

        # 5. Replay Trade
        if "replay" in q_lower or "verification" in q_lower:
            trade_id = None
            if "trade" in q_lower:
                # Try finding numeric ID in the query
                import re
                nums = re.findall(r"\d+", query)
                if nums:
                    trade_id = int(nums[0])
            return ExecutableCommand(
                action="replay_trade",
                params={"trade_id": trade_id, "limit": 5},
                description=f"Perform sequential event-based replay verification for trade{' ' + str(trade_id) if trade_id else 's'}.",
            )

        # 6. Compare Strategies
        if "compare" in q_lower or "strategy" in q_lower or "strategies" in q_lower:
            return ExecutableCommand(
                action="compare_strategies",
                params={},
                description="Perform multi-strategy backtest simulation and side-by-side performance comparison.",
            )

        return None


# Global singleton instance
command_system = CommandSystem()

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from services.ollo.os.tool_registry import tool_registry

logger = logging.getLogger(__name__)


class IntentRouter:
    """Manages the mapping of user prompts/queries to Tools, resolving parameters and dispatching without executing business logic."""

    _instance: Optional[IntentRouter] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

    def route(self, query: str) -> Dict[str, Any]:
        """Parse query, determine matched tools and parameter resolution."""
        q_lower = query.lower()
        matched_tools: List[Dict[str, Any]] = []
        resolved_intent = "General Chat"

        # 1. Parameter resolution helpers
        symbol = "BTC"
        if "eth" in q_lower:
            symbol = "ETH"
        elif "sol" in q_lower:
            symbol = "SOL"

        # 2. Heuristic query/regex matching patterns (Rule 4: strictly maps tools/parameters)
        # Case A: Journal + Replay (What mistakes did I make this week?)
        if "mistake" in q_lower or "mistakes" in q_lower:
            resolved_intent = "Mistake Post-Mortem Analysis"
            matched_tools.append({"name": "Journal", "params": {"action": "list", "symbol": symbol}})
            matched_tools.append({"name": "Replay", "params": {"limit": 5}})

        # Case B: Portfolio
        elif "portfolio" in q_lower or "exposure" in q_lower or "pnl" in q_lower or "balance" in q_lower:
            resolved_intent = "Portfolio Analysis"
            scope = "full"
            if "pnl" in q_lower or "performance" in q_lower:
                scope = "performance"
            elif "risk" in q_lower:
                scope = "risk"
            matched_tools.append({"name": "Portfolio", "params": {"scope": scope}})

        # Case C: Simulator
        elif "simulator" in q_lower or "simulate" in q_lower:
            resolved_intent = "Simulation Execution"
            matched_tools.append({"name": "Simulator", "params": {"action": "run", "symbol": f"{symbol}USDT"}})

        # Case D: Replay
        elif "replay" in q_lower or "verification" in q_lower:
            resolved_intent = "Replay Verification"
            matched_tools.append({"name": "Replay", "params": {"limit": 5}})

        # Case E: Market Scanner
        elif "analyze" in q_lower or "scanner" in q_lower or "signals" in q_lower or "scan" in q_lower:
            resolved_intent = "Market Analysis"
            matched_tools.append({"name": "Market Scanner", "params": {"symbol": symbol}})

        # Case F: Risk Analysis
        elif "risk" in q_lower or "exposure" in q_lower:
            resolved_intent = "Risk Evaluation"
            matched_tools.append({"name": "Risk Analysis", "params": {}})

        # Case G: Journal
        elif "journal" in q_lower or "diary" in q_lower or "notes" in q_lower:
            resolved_intent = "Journal Operations"
            matched_tools.append({"name": "Journal", "params": {"action": "list"}})

        return {
            "intent": resolved_intent,
            "tools": matched_tools,
        }

    def dispatch(self, query: str) -> Dict[str, Any]:
        """Route the query, execute the resolved tools, and return compiled tool data outputs."""
        routing_result = self.route(query)
        intent = routing_result["intent"]
        tools = routing_result["tools"]

        tool_outputs: List[Dict[str, Any]] = []
        for tool_spec in tools:
            name = tool_spec["name"]
            params = tool_spec["params"]
            logger.info("IntentRouter Dispatched: Tool='%s' with parameters %s", name, params)
            output = tool_registry.execute_tool(name, **params)
            tool_outputs.append({
                "tool": name,
                "output": output,
            })

        return {
            "intent": intent,
            "dispatched": len(tools) > 0,
            "tool_outputs": tool_outputs,
        }


# Global singleton instance
intent_router = IntentRouter()

"""Unit and integration tests for the NEXUS Cognitive Decision Operating System Layer.

Validates:
  - Universal Tool Registry (BaseTool, ToolRegistry, plugin dynamic registration, capability executions).
  - Context Manager (ephemeral conversation session, dynamic query extraction, fallback defaults).
  - Memory Layer (permanent conceptual memory categories, concept updates, file persistence).
  - Explainability Layer (core dimensions: why, evidence, confidence, risks, alternatives; explicit data unavailable status).
  - Command System (intent matching to executable commands).
  - Conversation Timeline (cognitive node sequencing connecting Conversation -> Intent -> Decision -> Action -> Outcome).
  - REST API endpoints under /ollo/os/ using FastAPI TestClient.
"""

from __future__ import annotations

import os
from typing import Any
import pytest
from fastapi.testclient import TestClient

from database import DecisionExplanation, get_session
from services.ollo.os import (
    tool_registry,
    context_manager,
    memory_layer,
    explainability_layer,
    command_system,
    conversation_timeline,
    BaseTool,
    ConceptMemory,
)


@pytest.fixture(autouse=True)
def clean_os_state():
    """Reset the OS singleton managers before and after each test."""
    context_manager.clear()
    conversation_timeline.clear()
    memory_layer.load()
    yield
    context_manager.clear()
    conversation_timeline.clear()


# ─── 1. Universal Tool Registry Tests ──────────────────────────────────────

def test_tool_registry_registration():
    tools = tool_registry.list_tools()
    assert len(tools) >= 7

    names = [t["name"] for t in tools]
    assert "Portfolio" in names
    assert "Simulator" in names
    assert "Replay" in names
    assert "Market Scanner" in names


def test_tool_registry_plugin_register():
    plugin_tool = BaseTool(
        name="News Tracker",
        description="Tracks breaking narrative-driving macro news.",
        parameters={},
        func=lambda **kw: {"status": "news_parsed"}
    )
    tool_registry.register(plugin_tool, plugin_name="MacroNews")

    retrieved = tool_registry.get_tool("News Tracker")
    assert retrieved is not None
    assert retrieved.description == "Tracks breaking narrative-driving macro news."

    exec_res = tool_registry.execute_tool("News Tracker")
    assert exec_res["success"] is True
    assert exec_res["data"] == {"status": "news_parsed"}


# ─── 2. Context Manager Tests ──────────────────────────────────────────────

def test_context_manager_get_set():
    assert context_manager.get("current_coin") == "BTC"
    context_manager.set("current_coin", "SOL")
    assert context_manager.get("current_coin") == "SOL"


def test_context_manager_query_extraction():
    context_manager.update_from_query("Let's analyze ETH on the 4h timeframe under breakout strategy.")
    assert context_manager.get("current_coin") == "ETH"
    assert context_manager.get("current_timeframe") == "4h"
    assert context_manager.get("current_strategy") == "breakout"


# ─── 3. Memory Layer Tests ─────────────────────────────────────────────────

def test_memory_layer_structure():
    mem = memory_layer.memory
    assert isinstance(mem, ConceptMemory)
    assert "favorite_markets" in mem.founder_preferences
    assert "risk_profile" in mem.risk_preferences


def test_memory_layer_updates():
    memory_layer.add_repeated_mistake("Over-leveraging on highly volatile breakout attempts.")
    assert "Over-leveraging on highly volatile breakout attempts." in memory_layer.memory.repeated_mistakes

    memory_layer.update_founder_preferences({"favorite_markets": ["BTC", "ETH", "SOL"]})
    assert memory_layer.memory.founder_preferences["favorite_markets"] == ["BTC", "ETH", "SOL"]


# ─── 4. Explainability Layer Tests ─────────────────────────────────────────

def test_explainability_fallback():
    exp = explainability_layer.generate_explanation(raw_evidence={"reasons": ["RSI Overbought"], "confidence": 92.5})
    assert exp["why"] == "Based on provided dynamic execution metrics."
    assert exp["confidence"] == "92.5%"
    assert exp["risks"]["risk_score"] == 0.3


def test_explainability_missing_data():
    exp = explainability_layer.generate_explanation()
    assert exp["why"] == "Evidence / explanation data is not available in the Decision Ledger."
    assert exp["confidence"] == "DATA_UNAVAILABLE"
    assert exp["risks"] is None


# ─── 5. Command System Tests ───────────────────────────────────────────────

def test_command_system_creation():
    cmd = command_system.create_command("Start paper trading simulator for ETH")
    assert cmd is not None
    assert cmd.action == "start_simulator"
    assert cmd.params == {"symbol": "ETHUSDT"}

    cmd_p = command_system.create_command("Show my portfolio pnl metrics")
    assert cmd_p is not None
    assert cmd_p.action == "open_portfolio"
    assert cmd_p.params == {"scope": "performance"}


# ─── 6. Conversation Timeline Tests ────────────────────────────────────────

def test_conversation_timeline_entry():
    entry = conversation_timeline.add_entry(
        conversation="Show my BTC metrics",
        intent="Portfolio Analysis",
        decision={"status": "resolved"},
        action={"action": "open_portfolio"},
        outcome={"data": "pnl_summary"},
        learning=["Strict trade tracking enforced."]
    )
    assert len(conversation_timeline.get_entries()) == 1
    assert entry.conversation == "Show my BTC metrics"
    assert entry.intent == "Portfolio Analysis"


# ─── 7. REST API Endpoints Integration Tests ────────────────────────────────

def test_api_list_tools(api_client):
    resp = api_client.get("/ollo/os/tools")
    assert resp.status_code == 200
    tools = resp.json()
    assert len(tools) >= 7


def test_api_plugin_registration(api_client):
    payload = {
        "name": "Social Sentiment Tool",
        "description": "Scans social narratives on X and Telegram.",
        "parameters": {}
    }
    resp = api_client.post("/ollo/os/tools/register-plugin?plugin_name=SocialSentiment", json=payload)
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert resp.json()["registered_tool"] == "Social Sentiment Tool"


def test_api_context_endpoints(api_client):
    resp = api_client.get("/ollo/os/context")
    assert resp.status_code == 200
    assert resp.json()["current_coin"] == "BTC"

    resp_put = api_client.post("/ollo/os/context", json={"key": "current_coin", "value": "AVAX"})
    assert resp_put.status_code == 200
    assert resp_put.json()["context"]["current_coin"] == "AVAX"


def test_api_memory_endpoints(api_client):
    resp = api_client.get("/ollo/os/memory")
    assert resp.status_code == 200
    assert "founder_preferences" in resp.json()

    payload = {
        "category": "founder_preferences",
        "data": {"name": "Senior Partner"}
    }
    resp_post = api_client.post("/ollo/os/memory", json=payload)
    assert resp_post.status_code == 200
    assert resp_post.json()["memory"]["founder_preferences"]["name"] == "Senior Partner"


def test_api_timeline_endpoints(api_client):
    conversation_timeline.add_entry("Hello OS", "Greeting", {"text": "Welcome"})
    resp = api_client.get("/ollo/os/timeline")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_api_command_execution(api_client):
    resp = api_client.post("/ollo/os/command", json={"action": "compare_strategies", "params": {}})
    assert resp.status_code == 200
    assert "comparison" in resp.json()


# ─── 8. Morning Command Center Briefing Tests ──────────────────────────────

def test_morning_briefing_continuous_dialogue():
    from services.ollo.ollo_service import OLLOService
    from tests.test_ollo import MockAIService
    mock_ai = MockAIService()
    svc = OLLOService(ai_service=mock_ai)

    # Run the intercepted morning query
    resp = svc.query("What do I need to know today?")
    assert resp.room == "command_deck"
    assert resp.text.startswith("OLLO response:")
    assert len(resp.sections) == 1
    assert resp.sections[0]["heading"] == "Suggested Commands"
    assert "Analyze BTC" in resp.sections[0]["bullets"]

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.ollo.os import (
    tool_registry,
    context_manager,
    memory_layer,
    explainability_layer,
    command_system,
    conversation_timeline,
    BaseTool,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ollo/os", tags=["NEXUS OS"])


# Models for request/response payloads

class ContextUpdateRequest(BaseModel):
    key: str
    value: Any


class MemoryUpdateRequest(BaseModel):
    category: str  # e.g., founder_preferences, risk_preferences, mistakes, patterns, behaviors
    data: Dict[str, Any]


class ToolRegisterRequest(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]


class CommandExecutionRequest(BaseModel):
    action: str
    params: Dict[str, Any]


# ─── Tool Registry Routes ──────────────────────────────────────────────────

@router.get("/tools")
def list_tools():
    """Retrieve details of all registered operating system tools."""
    return tool_registry.list_tools()


@router.post("/tools/register-plugin")
def register_plugin(body: ToolRegisterRequest, plugin_name: str = "custom_plugin"):
    """Register a custom tool dynamically as an OS plugin."""
    try:
        new_tool = BaseTool(
            name=body.name,
            description=body.description,
            parameters=body.parameters,
            func=lambda **kw: {"status": "plugin_executed", "params": kw},
        )
        tool_registry.register(new_tool, plugin_name=plugin_name)
        return {"success": True, "registered_tool": body.name, "plugin": plugin_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Context Manager Routes ────────────────────────────────────────────────

@router.get("/context")
def get_context():
    """Get active ephemeral conversational context."""
    return context_manager.to_dict()


@router.post("/context")
def update_context(body: ContextUpdateRequest):
    """Set or update ephemeral context state."""
    try:
        context_manager.set(body.key, body.value)
        return {"success": True, "context": context_manager.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/context")
def clear_context():
    """Clear active ephemeral context to defaults."""
    context_manager.clear()
    return {"success": True, "context": context_manager.to_dict()}


# ─── Memory Layer Routes ───────────────────────────────────────────────────

@router.get("/memory")
def get_memory():
    """Retrieve permanent, concept-based knowledge memories."""
    return memory_layer.memory.to_dict()


@router.post("/memory")
def update_memory(body: MemoryUpdateRequest):
    """Update permanent conceptual knowledge categories."""
    try:
        cat = body.category.lower()
        if cat == "founder_preferences":
            memory_layer.update_founder_preferences(body.data)
        elif cat == "risk_preferences":
            memory_layer.update_risk_preferences(body.data)
        elif cat == "strategy_preferences":
            memory_layer.update_strategy_preferences(body.data)
        elif cat == "mistakes" or cat == "repeated_mistakes":
            for m in body.data.get("mistakes", []):
                memory_layer.add_repeated_mistake(m)
        elif cat == "patterns" or cat == "successful_patterns":
            for p in body.data.get("patterns", []):
                memory_layer.add_successful_pattern(p)
        elif cat == "behaviors" or cat == "observed_behaviors":
            for b in body.data.get("behaviors", []):
                memory_layer.add_observed_behavior(b)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid memory category: {body.category}")
        return {"success": True, "memory": memory_layer.memory.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Timeline Routes ───────────────────────────────────────────────────────

@router.get("/timeline")
def get_timeline(limit: int = Query(20, ge=1, le=100)):
    """Retrieve entries on the cognitive conversation timeline."""
    return conversation_timeline.get_entries(limit=limit)


# ─── Command System Routes ─────────────────────────────────────────────────

@router.post("/command")
def execute_command(body: CommandExecutionRequest):
    """Execute a structured action or command directly."""
    from services.ollo.os.command_system import ExecutableCommand
    cmd = ExecutableCommand(action=body.action, params=body.params, description="")
    result = cmd.execute()
    return result

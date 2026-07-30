from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List

from core.nexus_brain.blackboard import CognitiveBlackboard, BlackboardEvent, EventPriority
from core.nexus_brain.memory import EpisodicMemory
from core.nexus_brain.guard import ConstraintGuard, GuardOutcome
from core.nexus_brain.learning import DecoupledCalibrationEngine, AdaptiveThresholdController
from core.nexus_brain.founder_platform import FounderPlatformCoordinator

router = APIRouter(prefix="/v1/nexus-brain", tags=["NEXUS_BRAIN"])

# Global Cognitive Context Registries (for demo/workspace interaction)
blackboard = CognitiveBlackboard()
memory_layer = EpisodicMemory()
guard = ConstraintGuard()
calibrator = DecoupledCalibrationEngine()
threshold_ctrl = AdaptiveThresholdController()
founder_ctrl = FounderPlatformCoordinator()

@router.get("/status")
def get_cognitive_status() -> Dict[str, Any]:
    """Exposes real-time active telemetry and operational parameters of NEXUS_BRAIN."""
    return {
        "status": "ONLINE",
        "phase": "PHASE_A",
        "blackboard_active_events_count": len(blackboard.queue),
        "episodic_memories_count": len(memory_layer.list_episodes()),
        "threshold": threshold_ctrl.current_threshold,
        "platform_telemetry": founder_ctrl.get_platform_telemetry()
    }

@router.post("/query-decision")
def evaluate_cognitive_decision(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulates a cognitive processing cycle through the Blackboard and runs Constraint Guard checks.
    """
    symbol = payload.get("symbol", "BTCUSDT")
    side = payload.get("side", "LONG")
    score = payload.get("score", 0.88)

    # 1. Post Ingestion Event to Blackboard
    ingest_ev = BlackboardEvent(
        event_type="SIGNAL_INGESTED",
        payload=payload,
        producer="REST_API",
        priority=EventPriority.HIGH
    )
    blackboard.post_event(ingest_ev)

    # 2. Confidence Calibration Check
    conf = calibrator.calculate_confidence(
        success_rate=0.80,
        agent_agreement=0.90,
        evidence_quality=0.85,
        uncertainty=0.15
    )

    # 3. Guard Gate Verification (Hard Constraints)
    active_count = payload.get("active_count", 1)
    exposure = payload.get("exposure", 50000.0)
    daily_loss = payload.get("daily_loss", 200.0)

    outcome, reasons = guard.evaluate(
        symbol=symbol,
        active_trades_count=active_count,
        symbol_exposure=exposure,
        current_daily_loss=daily_loss,
        score=score
    )

    # 4. Save Episodic Event Chain
    memory_layer.record_episode(
        signal_id=payload.get("signal_id", 42),
        symbol=symbol,
        side=side,
        score=score,
        confidence=conf,
        reasoning_chain=reasons,
        guard_status=outcome.value,
        event_chain=blackboard.get_replay_log().copy()
    )

    # 5. Clear active Blackboard queue for next run
    blackboard.clear()

    return {
        "decision": outcome.value,
        "calibrated_confidence": conf,
        "reasons": reasons,
        "replays_stored": len(memory_layer.list_episodes())
    }

@router.get("/replays")
def list_cognitive_replays() -> List[Dict[str, Any]]:
    """Lists stored cognitive decision lifecycles for full audit-replay and diagnostics."""
    return memory_layer.list_episodes()

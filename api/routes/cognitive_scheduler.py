from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.cognitive_scheduler import (
    CognitiveProcess,
    CognitiveScheduler,
    ResourceManifest,
    SharedVersionedQueue,
    SchedulingGuaranteeViolation,
    VersionValidationError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/scheduler", tags=["Cognitive Scheduler"])

# Singleton scheduler for the runtime
_scheduler = CognitiveScheduler()


def get_scheduler() -> CognitiveScheduler:
    return _scheduler


class ManifestSchema(BaseModel):
    default_cpu_share: float = 1.0
    ceiling_cpu_share: float = 1.0
    max_duration_seconds: float = 10.0
    max_memory_mb: float = 512.0


class ProcessCreateSchema(BaseModel):
    process_id: str
    name: str
    owner: str
    priority: int = 10
    manifest: Optional[ManifestSchema] = None
    channel_id: str = "default"


class ControlActionSchema(BaseModel):
    channel_id: str
    process_id: str


class DistributedSyncSchema(BaseModel):
    node_id: str
    processes: List[ProcessCreateSchema]


@router.get("/status")
def get_status() -> Dict[str, Any]:
    """Exposes real-time observability metrics and status of the cognitive scheduler."""
    sched = get_scheduler()
    return {
        "status": "active",
        "metrics": sched.get_observability_metrics()
    }


@router.post("/enqueue")
def enqueue_process(body: ProcessCreateSchema) -> Dict[str, Any]:
    """Enqueues a new cognitive process into the scheduler queue."""
    sched = get_scheduler()
    manifest_data = body.manifest or ManifestSchema()
    manifest = ResourceManifest(
        default_cpu_share=manifest_data.default_cpu_share,
        ceiling_cpu_share=manifest_data.ceiling_cpu_share,
        max_duration_seconds=manifest_data.max_duration_seconds,
        max_memory_mb=manifest_data.max_memory_mb,
    )
    proc = CognitiveProcess(
        process_id=body.process_id,
        name=body.name,
        owner=body.owner,
        priority=body.priority,
        manifest=manifest,
    )
    try:
        sched.enqueue_process(body.channel_id, proc)
        return {
            "success": True,
            "message": f"Successfully enqueued process {body.process_id}",
            "process": {
                "process_id": proc.process_id,
                "state": proc.state,
                "version": proc.version,
            }
        }
    except VersionValidationError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interrupt")
def interrupt_process(body: ControlActionSchema) -> Dict[str, Any]:
    """Triggers the real-time interrupt path to preempt a running process."""
    sched = get_scheduler()
    try:
        sched.interrupt_process(body.channel_id, body.process_id)
        return {
            "success": True,
            "message": f"Interrupt issued for process {body.process_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume")
def resume_process(body: ControlActionSchema) -> Dict[str, Any]:
    """Resumes a suspended process from its last checkpoint."""
    sched = get_scheduler()
    try:
        sched.resume_process(body.channel_id, body.process_id)
        return {
            "success": True,
            "message": f"Resume command issued for process {body.process_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/step")
def execute_scheduler_step(channel_id: str = "default") -> Dict[str, Any]:
    """Manually triggers a single scheduler execution tick for testing or step-by-step orchestration."""
    sched = get_scheduler()
    try:
        proc = sched.execute_step(channel_id)
        if proc:
            return {
                "success": True,
                "executed": {
                    "process_id": proc.process_id,
                    "state": proc.state,
                    "actual_duration": proc.actual_duration,
                    "actual_memory_mb": proc.actual_memory_mb,
                }
            }
        return {
            "success": True,
            "executed": None,
            "message": "Queue was empty."
        }
    except SchedulingGuaranteeViolation as e:
        raise HTTPException(status_code=422, detail=f"Guarantee Violation: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/degraded")
def trigger_degraded_mode(enable: bool = True) -> Dict[str, Any]:
    """Manually activates or deactivates scheduler degraded mode."""
    sched = get_scheduler()
    if enable:
        sched.enter_degraded_mode()
    else:
        sched.exit_degraded_mode()
    return {
        "success": True,
        "degraded_mode": sched.degraded_mode
    }


@router.post("/distributed/sync")
def distributed_sync(body: DistributedSyncSchema) -> Dict[str, Any]:
    """Distributed scheduling synchronization endpoint."""
    sched = get_scheduler()
    for item in body.processes:
        manifest_data = item.manifest or ManifestSchema()
        manifest = ResourceManifest(
            default_cpu_share=manifest_data.default_cpu_share,
            ceiling_cpu_share=manifest_data.ceiling_cpu_share,
            max_duration_seconds=manifest_data.max_duration_seconds,
            max_memory_mb=manifest_data.max_memory_mb,
        )
        proc = CognitiveProcess(
            process_id=item.process_id,
            name=item.name,
            owner=item.owner,
            priority=item.priority,
            manifest=manifest,
        )
        sched.enqueue_process(item.channel_id, proc)
    return {
        "success": True,
        "node_id": body.node_id,
        "synced_count": len(body.processes)
    }

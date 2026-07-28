from __future__ import annotations

import logging

from fastapi import APIRouter

from core.trust import TrustMetricsService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/trust/metrics")
def get_trust_metrics():
    """Retrieve derived trust metrics from the central, append-only Decision/Event Ledger."""
    service = TrustMetricsService()
    return service.calculate_metrics()

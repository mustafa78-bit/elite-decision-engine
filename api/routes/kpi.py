from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from services.kpi_service import KPIService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/kpi")
def get_kpis(request: Request):
    try:
        service = KPIService()
        kpis = service.get_kpis()
        return {"kpis": [k.to_dict() for k in kpis]}
    except Exception as e:
        logger.error("KPI endpoint failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api.dependencies import require_user_id
from services.kpi_service import KPIService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/kpi")
def get_kpis(request: Request):
    user_id = require_user_id(request)
    try:
        service = KPIService()
        kpis = service.get_kpis(user_id=user_id)
        return {"kpis": [k.to_dict() for k in kpis]}
    except Exception as e:
        logger.error("KPI endpoint failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})

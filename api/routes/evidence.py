from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_engine() -> Optional:
    try:
        from api.main import _evidence_engine
        return _evidence_engine
    except (ImportError, AttributeError):
        return None


@router.get("/evidence/latest")
def evidence_latest():
    engine = _get_engine()
    if engine is None:
        return JSONResponse(status_code=503, content={"error": "Evidence engine not initialized"})
    report = engine.latest()
    if report is None:
        return JSONResponse(status_code=404, content={"error": "No evidence reports available"})
    return report.to_dict()


@router.post("/evidence/build")
def evidence_build(
    symbol: str = "",
    recommendation: str = "",
    decision_result: Optional[dict[str, Any]] = None,
    risk_result: Optional[dict[str, Any]] = None,
    scanner_result: Optional[dict[str, Any]] = None,
    council_result: Optional[dict[str, Any]] = None,
    portfolio_result: Optional[dict[str, Any]] = None,
    market_regime_result: Optional[dict[str, Any]] = None,
    whale_result: Optional[list[dict[str, Any]]] = None,
    explain_result: Optional[dict[str, Any]] = None,
):
    engine = _get_engine()
    if engine is None:
        return JSONResponse(status_code=503, content={"error": "Evidence engine not initialized"})

    parsed = {}

    if decision_result is not None:
        parsed["decision_result"] = _dict_to_obj(decision_result)

    if risk_result is not None:
        parsed["risk_result"] = _dict_to_risk_obj(risk_result)

    if scanner_result is not None:
        parsed["scanner_result"] = _dict_to_obj(scanner_result)

    if council_result is not None:
        parsed["council_result"] = _dict_to_obj(council_result)

    if portfolio_result is not None:
        parsed["portfolio_result"] = _dict_to_obj(portfolio_result)

    if market_regime_result is not None:
        parsed["market_regime_result"] = market_regime_result

    if whale_result is not None:
        parsed["whale_result"] = whale_result

    if explain_result is not None:
        parsed["explain_result"] = _dict_to_obj(explain_result)

    try:
        report = engine.build(
            **parsed,
            symbol=symbol,
            recommendation=recommendation,
        )
        return report.to_dict()
    except Exception as e:
        logger.exception("Evidence build failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/evidence/{decision_id}")
def evidence_get(decision_id: str):
    engine = _get_engine()
    if engine is None:
        return JSONResponse(status_code=503, content={"error": "Evidence engine not initialized"})
    report = engine.get(decision_id)
    if report is None:
        return JSONResponse(status_code=404, content={"error": f"Report {decision_id} not found"})
    return report.to_dict()


@router.get("/evidence/timeline/{decision_id}")
def evidence_timeline(decision_id: str):
    engine = _get_engine()
    if engine is None:
        return JSONResponse(status_code=503, content={"error": "Evidence engine not initialized"})
    timeline = engine.timeline(decision_id)
    if not timeline:
        return JSONResponse(status_code=404, content={"error": f"No timeline for {decision_id}"})
    return {"decision_id": decision_id, "events": timeline}


def _dict_to_obj(d: dict[str, Any]) -> Any:
    class DictObj:
        def __init__(self, data: dict[str, Any]) -> None:
            self._data = data

        def __getattr__(self, name: str) -> Any:
            return self._data.get(name)

    return DictObj(d)


def _dict_to_risk_obj(d: dict[str, Any]) -> Any:
    checks_raw = d.get("checks", [])
    parsed_checks = []
    for c in checks_raw:
        if isinstance(c, dict):
            parsed_checks.append(_dict_to_obj(c))
        else:
            parsed_checks.append(c)
    d["checks"] = parsed_checks
    return _dict_to_obj(d)

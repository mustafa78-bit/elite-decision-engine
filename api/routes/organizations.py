from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel

from services.organization_service import OrganizationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/organizations")


# ------------------------------------------------------------------
# PYDANTIC DTO SCHEMAS
# ------------------------------------------------------------------

class OrganizationCreate(BaseModel):
    name: str
    tenant_id: str


class OrganizationResponse(BaseModel):
    id: int
    name: str
    tenant_id: str
    status: str
    created_at: Optional[datetime] = None


class WorkspaceCreate(BaseModel):
    name: str
    config: dict = {}


class WorkspaceResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    config: dict
    created_at: Optional[datetime] = None


class APIKeyCreate(BaseModel):
    name: str
    expires_in_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class APIKeyWithRawResponse(BaseModel):
    raw_key: str
    key_info: APIKeyResponse


class AssignRoleRequest(BaseModel):
    user_id: int
    role: str # ADMIN, TRADER, OBSERVER


class RoleResponse(BaseModel):
    id: int
    user_id: int
    organization_id: int
    role: str
    created_at: Optional[datetime] = None


class AuditLogResponse(BaseModel):
    id: int
    organization_id: int
    user_id: Optional[int] = None
    action: str
    details: dict
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None


# ------------------------------------------------------------------
# DEPENDENCIES / HELPER
# ------------------------------------------------------------------

def get_org_service() -> OrganizationService:
    return OrganizationService()


async def verify_enterprise_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    svc: OrganizationService = Depends(get_org_service),
) -> dict[str, Any]:
    """
    Middleware-like dependency verifying the incoming enterprise request has a valid api key.
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header is missing.")

    org = svc.authenticate_api_key(x_api_key)
    if not org:
        raise HTTPException(status_code=403, detail="Invalid, expired, or deactivated API key.")

    return org


# ------------------------------------------------------------------
# ROUTE ENDPOINTS
# ------------------------------------------------------------------

@router.post("", response_model=OrganizationResponse, status_code=201)
def create_organization(body: OrganizationCreate, svc: OrganizationService = Depends(get_org_service)):
    try:
        org = svc.create_organization(body.name, body.tenant_id)
        return org
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal database error: {e}")


@router.get("/{organization_id}", response_model=OrganizationResponse)
def get_organization(organization_id: int, svc: OrganizationService = Depends(get_org_service)):
    org = svc.get_organization(organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.post("/{organization_id}/workspaces", response_model=WorkspaceResponse, status_code=201)
def create_workspace(
    organization_id: int, body: WorkspaceCreate, svc: OrganizationService = Depends(get_org_service)
):
    try:
        ws = svc.create_workspace(organization_id, body.name, body.config)
        svc.log_audit_action(
            organization_id=organization_id,
            action="WORKSPACE_CREATE",
            details={"workspace_name": body.name},
        )
        return ws
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{organization_id}/workspaces", response_model=List[WorkspaceResponse])
def get_workspaces(organization_id: int, svc: OrganizationService = Depends(get_org_service)):
    return svc.get_workspaces(organization_id)


@router.post("/{organization_id}/keys", response_model=APIKeyWithRawResponse, status_code=201)
def generate_api_key(
    organization_id: int, body: APIKeyCreate, svc: OrganizationService = Depends(get_org_service)
):
    try:
        raw_key, key_info = svc.generate_api_key(organization_id, body.name, body.expires_in_days)
        svc.log_audit_action(
            organization_id=organization_id,
            action="API_KEY_GENERATE",
            details={"key_name": body.name},
        )
        return APIKeyWithRawResponse(raw_key=raw_key, key_info=key_info)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{organization_id}/roles", response_model=RoleResponse)
def assign_role(
    organization_id: int, body: AssignRoleRequest, svc: OrganizationService = Depends(get_org_service)
):
    try:
        role_record = svc.assign_user_role(body.user_id, organization_id, body.role)
        svc.log_audit_action(
            organization_id=organization_id,
            action="ROLE_ASSIGN",
            details={"user_id": body.user_id, "role": body.role},
        )
        return role_record
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{organization_id}/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(organization_id: int, svc: OrganizationService = Depends(get_org_service)):
    return svc.get_audit_logs(organization_id)


@router.get("/secure/me", response_model=OrganizationResponse)
def get_authenticated_organization(org: dict[str, Any] = Depends(verify_enterprise_api_key)):
    """
    Endpoint protected by X-API-Key interceptor.
    """
    return org

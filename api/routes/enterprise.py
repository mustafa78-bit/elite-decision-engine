from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header, Request, Body
from pydantic import BaseModel, EmailStr

import database
from database import User
from enterprise.auth import (
    register_enterprise_user,
    login_enterprise_user,
    verify_email,
    refresh_access_token,
    recover_password_request,
    reset_password_with_token
)
from enterprise.rbac import PermissionService, check_permissions
from enterprise.workspace import (
    create_organization,
    create_team,
    add_organization_member,
    send_team_invitation,
    accept_team_invitation,
    get_organization_members
)
from enterprise.api_keys import (
    generate_api_key,
    rotate_api_key,
    validate_api_key,
    check_rate_limit,
    register_webhook,
    deliver_webhook
)
from enterprise.audit import log_action, search_audit_logs
from enterprise.billing import create_subscription, check_feature_gate, generate_invoice
from enterprise.monitoring import get_system_health_metrics

router = APIRouter(prefix="/api/v1/enterprise", tags=["Enterprise"])


# ─── Schemas ───────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: Optional[str] = "Viewer"

class LoginRequest(BaseModel):
    username: str
    password: str

class PasswordRecoveryRequest(BaseModel):
    email: str

class PasswordResetRequest(BaseModel):
    token: str
    new_password: str

class OrganizationCreateRequest(BaseModel):
    name: str
    user_id: int

class TeamCreateRequest(BaseModel):
    name: str

class InvitationSendRequest(BaseModel):
    email: str
    role: str
    team_id: Optional[int] = None

class APIKeyCreateRequest(BaseModel):
    user_id: int
    organization_id: Optional[int] = None
    name: str

class WebhookRegisterRequest(BaseModel):
    url: str
    events: List[str]

class DeliverWebhookRequest(BaseModel):
    event_type: str
    payload: dict

class SubscriptionCreateRequest(BaseModel):
    tier: str

class InvoiceCreateRequest(BaseModel):
    subscription_id: int
    amount: float


# ─── Auth Endpoints ────────────────────────────────────────────────────────

@router.post("/auth/register")
def register(body: RegisterRequest):
    res = register_enterprise_user(body.username, body.email, body.password, body.role)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@router.post("/auth/login")
def login(request: Request, body: LoginRequest):
    user_agent = request.headers.get("User-Agent", "")
    ip_address = request.client.host if request.client else ""
    res = login_enterprise_user(body.username, body.password, user_agent, ip_address)
    if not res["success"]:
        raise HTTPException(status_code=401, detail=res["error"])
    return res

@router.get("/auth/verify")
def verify(token: str = Query(...)):
    res = verify_email(token)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@router.post("/auth/refresh")
def refresh(refresh_token: str = Body(..., embed=True)):
    res = refresh_access_token(refresh_token)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@router.post("/auth/recover")
def recover(body: PasswordRecoveryRequest):
    res = recover_password_request(body.email)
    return res

@router.post("/auth/reset")
def reset_password(body: PasswordResetRequest):
    res = reset_password_with_token(body.token, body.new_password)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res


# ─── Workspace Endpoints (RBAC protected) ──────────────────────────────────

@router.post("/organizations")
def create_org(body: OrganizationCreateRequest, x_user_role: str = Header("Viewer")):
    # Require Admin or above to create organization
    PermissionService.authorize(x_user_role, "delete_organization")  # Founder level gating
    res = create_organization(body.name, body.user_id)
    return res

@router.post("/organizations/{org_id}/teams")
def create_org_team(org_id: int, body: TeamCreateRequest, x_user_role: str = Header("Viewer")):
    PermissionService.authorize(x_user_role, "manage_teams")
    res = create_team(org_id, body.name)
    return res

@router.post("/organizations/{org_id}/invitations")
def send_invite(org_id: int, body: InvitationSendRequest, x_user_role: str = Header("Viewer")):
    PermissionService.authorize(x_user_role, "invite_member")
    res = send_team_invitation(org_id, body.email, body.role, body.team_id)
    return res

@router.post("/invitations/accept")
def accept_invite(token: str = Query(...), user_id: int = Query(...)):
    res = accept_team_invitation(token, user_id)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@router.get("/organizations/{org_id}/members")
def list_members(org_id: int, x_user_role: str = Header("Viewer")):
    PermissionService.authorize(x_user_role, "read_reports")
    return get_organization_members(org_id)


# ─── API Key & Integration Endpoints ───────────────────────────────────────

@router.post("/api-keys")
def generate_key(body: APIKeyCreateRequest, x_user_role: str = Header("Viewer")):
    PermissionService.authorize(x_user_role, "generate_keys")
    res = generate_api_key(body.user_id, body.organization_id, body.name)
    return res

@router.post("/api-keys/{key_id}/rotate")
def rotate_key(key_id: int, x_user_role: str = Header("Viewer")):
    PermissionService.authorize(x_user_role, "rotate_keys")
    res = rotate_api_key(key_id)
    return res

@router.get("/api-keys/validate")
def validate_key(api_key: str = Query(...)):
    res = validate_api_key(api_key)
    if not res["success"]:
        raise HTTPException(status_code=401, detail=res["error"])
    return res

@router.get("/api-keys/check-rate")
def check_key_rate(api_key: str = Query(...), limit: int = Query(5)):
    # Simulates rate limit middleware check
    res = check_rate_limit(api_key, limit=limit)
    if not res["success"]:
        raise HTTPException(status_code=429, detail=res["error"])
    return res

@router.post("/organizations/{org_id}/webhooks")
def register_org_webhook(org_id: int, body: WebhookRegisterRequest, x_user_role: str = Header("Viewer")):
    PermissionService.authorize(x_user_role, "configure_webhooks")
    res = register_webhook(org_id, body.url, body.events)
    return res

@router.post("/webhooks/{webhook_id}/deliver")
def test_deliver_webhook(webhook_id: int, body: DeliverWebhookRequest, x_user_role: str = Header("Viewer")):
    PermissionService.authorize(x_user_role, "configure_webhooks")
    res = deliver_webhook(webhook_id, body.event_type, body.payload)
    return res


# ─── Audit Endpoints ───────────────────────────────────────────────────────

@router.get("/audit-logs")
def get_audit(
    action: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    organization_id: Optional[int] = Query(None),
    x_user_role: str = Header("Viewer")
):
    PermissionService.authorize(x_user_role, "view_audit_logs")
    return search_audit_logs(user_id=user_id, organization_id=organization_id, action=action)


# ─── Billing Endpoints ─────────────────────────────────────────────────────

@router.post("/organizations/{org_id}/subscription")
def create_org_sub(org_id: int, body: SubscriptionCreateRequest, x_user_role: str = Header("Viewer")):
    PermissionService.authorize(x_user_role, "manage_billing")
    res = create_subscription(org_id, body.tier)
    return res

@router.get("/organizations/{org_id}/features/check")
def check_gate(org_id: int, feature: str = Query(...)):
    has_access = check_feature_gate(org_id, feature)
    return {"feature": feature, "has_access": has_access}

@router.post("/organizations/{org_id}/invoices")
def create_org_invoice(org_id: int, body: InvoiceCreateRequest, x_user_role: str = Header("Viewer")):
    PermissionService.authorize(x_user_role, "manage_billing")
    res = generate_invoice(org_id, body.subscription_id, body.amount)
    return res


# ─── Monitoring & Observability Endpoints ──────────────────────────────────

@router.get("/monitoring")
def get_monitoring(x_user_role: str = Header("Viewer")):
    # Observability is accessible to viewers and above
    PermissionService.authorize(x_user_role, "view_dashboard")
    return get_system_health_metrics()

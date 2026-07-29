import pytest
from datetime import datetime, timezone, timedelta
from database import (
    Organization,
    UserOrganizationRole,
    TeamWorkspace,
    EnterpriseAPIKey,
    EnterpriseAuditLog,
)
from services.organization_service import OrganizationService


# ─── Organization & Tenant Tests ──────────────────────────────────────────────

def test_organization_creation_and_retrieval(db_session):
    svc = OrganizationService(session_factory=lambda: db_session)

    # Success Flow
    org = svc.create_organization(name="Acme Corp", tenant_id="acme")
    assert org["id"] is not None
    assert org["name"] == "Acme Corp"
    assert org["tenant_id"] == "acme"
    assert org["status"] == "ACTIVE"

    # Duplicate Tenant ID Flow
    with pytest.raises(ValueError, match="already exists"):
        svc.create_organization(name="Acme 2", tenant_id="acme")

    # Get by ID
    retrieved = svc.get_organization(org["id"])
    assert retrieved is not None
    assert retrieved["name"] == "Acme Corp"

    # Get by Tenant ID
    retrieved_tenant = svc.get_organization_by_tenant("acme")
    assert retrieved_tenant is not None
    assert retrieved_tenant["id"] == org["id"]


# ─── RBAC & Workspace Tests ───────────────────────────────────────────────────

def test_rbac_and_workspaces(db_session):
    svc = OrganizationService(session_factory=lambda: db_session)

    org = svc.create_organization(name="Initech", tenant_id="initech")
    org_id = org["id"]

    # Assign and verify role
    role_rec = svc.assign_user_role(user_id=101, organization_id=org_id, role="ADMIN")
    assert role_rec["role"] == "ADMIN"
    assert role_rec["user_id"] == 101

    role = svc.get_user_role(user_id=101, organization_id=org_id)
    assert role == "ADMIN"

    # Update role
    svc.assign_user_role(user_id=101, organization_id=org_id, role="TRADER")
    role_updated = svc.get_user_role(user_id=101, organization_id=org_id)
    assert role_updated == "TRADER"

    # Non-existent org role assignment should fail
    with pytest.raises(ValueError, match="does not exist"):
        svc.assign_user_role(user_id=101, organization_id=99999, role="ADMIN")

    # Create workspace
    ws = svc.create_workspace(organization_id=org_id, name="Quantitative Fund A", config={"leverage_limit": 5})
    assert ws["id"] is not None
    assert ws["name"] == "Quantitative Fund A"
    assert ws["config"] == {"leverage_limit": 5}

    # Fetch workspaces
    workspaces = svc.get_workspaces(org_id)
    assert len(workspaces) == 1
    assert workspaces[0]["id"] == ws["id"]


# ─── Security (API Keys) & Cryptographic Tests ────────────────────────────────

def test_api_key_lifecycle_and_authentication(db_session):
    svc = OrganizationService(session_factory=lambda: db_session)

    org = svc.create_organization(name="Hooli", tenant_id="hooli")
    org_id = org["id"]

    # Generate API key
    raw_key, key_info = svc.generate_api_key(organization_id=org_id, name="Default Key", expires_in_days=30)
    assert raw_key.startswith("nx_")
    assert key_info["name"] == "Default Key"
    assert key_info["is_active"] is True
    assert key_info["expires_at"] is not None

    # Authenticate successfully
    auth_org = svc.authenticate_api_key(raw_key)
    assert auth_org is not None
    assert auth_org["id"] == org_id
    assert auth_org["tenant_id"] == "hooli"

    # Invalidate key by setting active = False
    key_rec = db_session.query(EnterpriseAPIKey).filter(EnterpriseAPIKey.id == key_info["id"]).first()
    key_rec.is_active = False
    db_session.flush()

    # Authenticate should fail
    assert svc.authenticate_api_key(raw_key) is None

    # Revived key but expired should fail authentication
    key_rec.is_active = True
    key_rec.expires_at = datetime.now() - timedelta(days=1)
    db_session.flush()

    assert svc.authenticate_api_key(raw_key) is None


# ─── Audit Trail Tests ────────────────────────────────────────────────────────

def test_audit_logging_and_history(db_session):
    svc = OrganizationService(session_factory=lambda: db_session)

    org = svc.create_organization(name="Weyland-Yutani", tenant_id="weyland")
    org_id = org["id"]

    # Log action
    log = svc.log_audit_action(
        organization_id=org_id,
        action="POSITION_SIZING_RULE_UPDATE",
        user_id=202,
        details={"max_leverage_adjusted": 20},
        ip_address="192.168.1.100"
    )

    assert log["id"] is not None
    assert log["action"] == "POSITION_SIZING_RULE_UPDATE"
    assert log["user_id"] == 202
    assert log["details"] == {"max_leverage_adjusted": 20}
    assert log["ip_address"] == "192.168.1.100"

    # Fetch logs
    logs = svc.get_audit_logs(org_id)
    assert len(logs) == 1
    assert logs[0]["id"] == log["id"]


# ─── REST API Endpoints Integration Tests ─────────────────────────────────────

def test_organizations_api_endpoints(api_client, db_session):
    # 1. Create Organization via REST
    resp = api_client.post(
        "/api/v1/organizations",
        json={"name": "Cyberdyne Systems", "tenant_id": "cyberdyne"}
    )
    assert resp.status_code == 201
    org_data = resp.json()
    assert org_data["name"] == "Cyberdyne Systems"
    assert org_data["tenant_id"] == "cyberdyne"
    org_id = org_data["id"]

    # 2. Get Organization via REST
    resp = api_client.get(f"/api/v1/organizations/{org_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Cyberdyne Systems"

    # 3. Create Workspace via REST
    resp = api_client.post(
        f"/api/v1/organizations/{org_id}/workspaces",
        json={"name": "Skynet Core", "config": {"neural_net_enabled": True}}
    )
    assert resp.status_code == 201
    ws_data = resp.json()
    assert ws_data["name"] == "Skynet Core"
    assert ws_data["config"] == {"neural_net_enabled": True}

    # 4. Fetch Workspaces via REST
    resp = api_client.get(f"/api/v1/organizations/{org_id}/workspaces")
    assert resp.status_code == 200
    workspaces = resp.json()
    assert len(workspaces) == 1
    assert workspaces[0]["id"] == ws_data["id"]

    # 5. Generate API Key via REST
    resp = api_client.post(
        f"/api/v1/organizations/{org_id}/keys",
        json={"name": "Skynet Admin Key", "expires_in_days": 10}
    )
    assert resp.status_code == 201
    key_payload = resp.json()
    assert "raw_key" in key_payload
    raw_key = key_payload["raw_key"]
    assert key_payload["key_info"]["name"] == "Skynet Admin Key"

    # 6. Assign role via REST
    resp = api_client.post(
        f"/api/v1/organizations/{org_id}/roles",
        json={"user_id": 999, "role": "OBSERVER"}
    )
    assert resp.status_code == 200
    role_data = resp.json()
    assert role_data["user_id"] == 999
    assert role_data["role"] == "OBSERVER"

    # 7. Get Audit Logs via REST
    resp = api_client.get(f"/api/v1/organizations/{org_id}/audit-logs")
    assert resp.status_code == 200
    audit_logs = resp.json()
    # Should have logs for workspace creation, key generation, role assignment
    assert len(audit_logs) >= 3
    actions = [log["action"] for log in audit_logs]
    assert "WORKSPACE_CREATE" in actions
    assert "API_KEY_GENERATE" in actions
    assert "ROLE_ASSIGN" in actions

    # 8. Test Authenticated Route with X-API-Key Interception
    # Call secure endpoint without key
    resp_unauth = api_client.get("/api/v1/organizations/secure/me")
    assert resp_unauth.status_code == 401 # Missing X-API-Key

    # Call with invalid key
    resp_forbidden = api_client.get("/api/v1/organizations/secure/me", headers={"X-API-Key": "invalid_key"})
    assert resp_forbidden.status_code == 403 # Forbidden

    # Call with valid key
    resp_secure = api_client.get("/api/v1/organizations/secure/me", headers={"X-API-Key": raw_key})
    assert resp_secure.status_code == 200
    secured_org = resp_secure.json()
    assert secured_org["id"] == org_id
    assert secured_org["name"] == "Cyberdyne Systems"

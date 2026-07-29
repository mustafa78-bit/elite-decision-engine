import pytest
from datetime import datetime, timezone
import secrets

from database import User, get_session, create_tables
from enterprise.auth import (
    register_enterprise_user,
    verify_email,
    login_enterprise_user,
    refresh_access_token,
    recover_password_request,
    reset_password_with_token
)
from enterprise.rbac import (
    Role,
    check_permissions,
    has_role_or_above,
    has_permission
)
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
from enterprise.billing import (
    SubscriptionTier,
    create_subscription,
    check_feature_gate,
    generate_invoice
)
from enterprise.monitoring import get_system_health_metrics


pytestmark = pytest.mark.usefixtures("db_session")


# ─── EPIC 1: IAM TESTS ───────────────────────────────────────────────────────

def test_auth_registration(db_session):
    res = register_enterprise_user("boss", "boss@nexus.io", "strongpass123", "Founder")
    assert res["success"] is True
    assert res["user"]["role"] == "Founder"
    assert res["user"]["is_verified"] is False
    assert res["verification_token"] is not None

def test_auth_email_verification(db_session):
    res = register_enterprise_user("analyst", "analyst@nexus.io", "pass123", "Analyst")
    token = res["verification_token"]

    v_res = verify_email(token)
    assert v_res["success"] is True
    assert v_res["message"] == "Email verified successfully"

def test_auth_lockout_mechanism(db_session):
    # Register user
    register_enterprise_user("locked_user", "lock@nexus.io", "correct_pass", "Trader")

    # Fail login 5 times
    for _ in range(5):
        login_res = login_enterprise_user("locked_user", "wrong_pass")
        assert login_res["success"] is False

    # Check that account is locked
    locked_res = login_enterprise_user("locked_user", "correct_pass")
    assert locked_res["success"] is False
    assert "locked" in locked_res["error"].lower()
    assert locked_res["is_locked"] is True

def test_auth_refresh_token(db_session):
    register_enterprise_user("trader", "trader@nexus.io", "correct_pass", "Trader")
    login_res = login_enterprise_user("trader", "correct_pass")
    assert login_res["success"] is True
    ref_token = login_res["refresh_token"]

    # Refresh
    ref_res = refresh_access_token(ref_token)
    assert ref_res["success"] is True
    assert ref_res["access_token"] is not None
    assert ref_res["refresh_token"] != ref_token

def test_auth_password_recovery(db_session):
    register_enterprise_user("forgetful", "forget@nexus.io", "correct_pass", "Viewer")
    rec_res = recover_password_request("forget@nexus.io")
    assert rec_res["success"] is True
    rec_token = rec_res["recovery_token"]

    # Reset password
    reset_res = reset_password_with_token(rec_token, "new_secure_pass")
    assert reset_res["success"] is True

    # Try logging in with new pass
    login_res = login_enterprise_user("forgetful", "new_secure_pass")
    assert login_res["success"] is True


# ─── EPIC 2: RBAC TESTS ──────────────────────────────────────────────────────

def test_rbac_inheritance(db_session):
    # Roles: Founder > Admin > Analyst > Trader > Viewer
    assert has_role_or_above("Founder", Role.FOUNDER) is True
    assert has_role_or_above("Founder", Role.VIEWER) is True
    assert has_role_or_above("Viewer", Role.FOUNDER) is False
    assert has_role_or_above("Analyst", Role.TRADER) is True
    assert has_role_or_above("Trader", Role.ANALYST) is False

def test_rbac_permissions(db_session):
    assert has_permission("Founder", "execute_trade") is True
    assert has_permission("Admin", "invite_member") is True
    assert has_permission("Trader", "execute_trade") is True
    assert has_permission("Trader", "invite_member") is False
    assert has_permission("Viewer", "view_dashboard") is True
    assert has_permission("Viewer", "execute_trade") is False


# ─── EPIC 3: WORKSPACE & TEAMS TESTS ──────────────────────────────────────────

def test_workspace_organization_creation(db_session):
    org_res = create_organization("NEXUS Corp", user_id=1)
    assert org_res["success"] is True
    assert org_res["organization"]["name"] == "NEXUS Corp"

def test_workspace_team_creation(db_session):
    org_res = create_organization("NEXUS Corp", user_id=1)
    org_id = org_res["organization"]["id"]

    team_res = create_team(org_id, "Alpha Quant Team")
    assert team_res["success"] is True
    assert team_res["team"]["name"] == "Alpha Quant Team"

def test_workspace_member_invitation_flow(db_session):
    # Register Owner
    owner_res = register_enterprise_user("owner", "owner@nexus.io", "pass123", "Founder")
    owner_id = owner_res["user"]["id"]
    org_res = create_organization("NEXUS Corp", user_id=owner_id)
    org_id = org_res["organization"]["id"]

    # Invite
    inv_res = send_team_invitation(org_id, email="invitee@nexus.io", role="Analyst")
    assert inv_res["success"] is True
    token = inv_res["invitation"]["token"]

    # Accept invitation as a new user
    user_res = register_enterprise_user("invitee", "invitee@nexus.io", "pass123")
    user_id = user_res["user"]["id"]

    accept_res = accept_team_invitation(token, user_id)
    assert accept_res["success"] is True

    # Verify they are a member
    members = get_organization_members(org_id)
    assert len(members) == 2  # Owner + Invitee
    assert any(m["user_id"] == user_id and m["role"] == "Analyst" for m in members)


# ─── EPIC 4: API KEYS & WEBHOOKS TESTS ────────────────────────────────────────

def test_api_key_generation_and_validation(db_session):
    key_res = generate_api_key(user_id=1, organization_id=1, name="TradingView key")
    assert key_res["success"] is True
    api_key_str = key_res["api_key"]
    assert api_key_str.startswith("nx_")

    # Validate
    val_res = validate_api_key(api_key_str)
    assert val_res["success"] is True
    assert val_res["user_id"] == 1

def test_api_key_rotation(db_session):
    key_res = generate_api_key(user_id=1, organization_id=1, name="Slack bot key")
    api_key_str = key_res["api_key"]
    key_id = key_res["id"]

    rot_res = rotate_api_key(key_id)
    assert rot_res["success"] is True
    new_key_str = rot_res["api_key"]
    assert new_key_str != api_key_str

    # Old key invalid
    assert validate_api_key(api_key_str)["success"] is False
    # New key valid
    assert validate_api_key(new_key_str)["success"] is True

def test_api_key_rate_limiting(db_session):
    # Allowed 5 requests
    for _ in range(5):
        assert check_rate_limit(api_key="nx_test", limit=5)["success"] is True
    # 6th request fails
    assert check_rate_limit(api_key="nx_test", limit=5)["success"] is False

def test_webhook_delivery(db_session):
    web_res = register_webhook(organization_id=1, url="https://example.com/webhook", events=["trade.executed"])
    assert web_res["success"] is True
    webhook_id = web_res["webhook"]["id"]

    # Deliver
    del_res = deliver_webhook(webhook_id, event_type="trade.executed", payload={"pnl": 500.0})
    assert del_res["success"] is True
    assert del_res["status_code"] == 200


# ─── EPIC 5: AUDIT LOGS TESTS ────────────────────────────────────────────────

def test_audit_logs(db_session):
    log_action(user_id=1, organization_id=1, action="User Login", details={"ip": "127.0.0.1"})
    log_action(user_id=1, organization_id=1, action="Execute Trade", details={"symbol": "BTC"})

    # Search
    results = search_audit_logs(action="Execute Trade")
    assert len(results) == 1
    assert results[0]["action"] == "Execute Trade"


# ─── EPIC 7: SUBSCRIPTIONS & GATING TESTS ────────────────────────────────────

def test_subscription_feature_gating(db_session):
    create_subscription(organization_id=1, tier=SubscriptionTier.PRO)

    # Pro cannot access enterprise-only tools
    assert check_feature_gate(organization_id=1, feature="advanced_analytics") is True
    assert check_feature_gate(organization_id=1, feature="multi_org_control") is False

def test_invoice_generation(db_session):
    sub_res = create_subscription(organization_id=1, tier=SubscriptionTier.ENTERPRISE)
    sub_id = sub_res["subscription"]["id"]

    inv_res = generate_invoice(organization_id=1, subscription_id=sub_id, amount=999.0)
    assert inv_res["success"] is True
    assert inv_res["invoice"]["amount"] == 999.0
    assert inv_res["invoice"]["status"] == "unpaid"


# ─── EPIC 8: MONITORING & METRICS TESTS ──────────────────────────────────────

def test_system_monitoring_metrics(db_session):
    metrics = get_system_health_metrics()
    assert "health" in metrics
    assert "metrics" in metrics
    assert metrics["health"]["database_status"] == "connected"
    assert "cpu_utilization" in metrics["metrics"]

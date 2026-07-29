from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class Role:
    FOUNDER = "Founder"
    ADMIN = "Admin"
    ANALYST = "Analyst"
    TRADER = "Trader"
    VIEWER = "Viewer"

# Role rank for inheritance (higher rank inherits all permissions of lower ranks)
ROLE_RANK = {
    Role.VIEWER: 1,
    Role.TRADER: 2,
    Role.ANALYST: 3,
    Role.ADMIN: 4,
    Role.FOUNDER: 5
}

# Explicit permissions defined per role level
ROLE_PERMISSIONS = {
    Role.VIEWER: {
        "view_dashboard",
        "read_reports",
        "read_alerts",
        "read_watchlists",
        "read_positions"
    },
    Role.TRADER: {
        "execute_trade",
        "cancel_order",
        "create_journal",
        "view_journal"
    },
    Role.ANALYST: {
        "generate_intelligence",
        "rank_opportunities",
        "run_backtest",
        "create_watchlist"
    },
    Role.ADMIN: {
        "invite_member",
        "manage_teams",
        "configure_webhooks",
        "rotate_keys",
        "view_audit_logs",
        "generate_keys"
    },
    Role.FOUNDER: {
        "manage_billing",
        "multi_org_control",
        "seal_ledger",
        "delete_organization"
    }
}

def has_role_or_above(user_role: str, target_role: str) -> bool:
    """Return True if user_role has rank equal or greater than target_role."""
    if not user_role or not target_role:
        return False
    user_rank = ROLE_RANK.get(user_role, 0)
    target_rank = ROLE_RANK.get(target_role, 0)
    return user_rank >= target_rank

def has_permission(user_role: str, permission: str) -> bool:
    """Check if the user_role is authorized for the given permission based on role inheritance."""
    if not user_role:
        return False

    user_rank = ROLE_RANK.get(user_role, 0)

    # Check permissions of current role and all inherited roles (lower ranks)
    for role, rank in ROLE_RANK.items():
        if user_rank >= rank:
            if permission in ROLE_PERMISSIONS.get(role, set()):
                return True

    return False


class PermissionService:
    """Centralized authorization layer and permission engine."""

    @staticmethod
    def authorize(user_role: str, permission: str) -> None:
        """Validate permission, raise 403 HTTP Exception on unauthorized."""
        if not has_permission(user_role, permission):
            logger.warning("RBAC Auth Failure: role %s tried to access %s without authorization", user_role, permission)
            raise HTTPException(
                status_code=403,
                detail=f"Action Forbidden: Role {user_role} does not possess {permission} permission."
            )

    @staticmethod
    def check_feature_flag(user_role: str, feature: str) -> bool:
        """Verify feature accessibility based on role capability."""
        # Simple policy: feature maps directly to permission mapping
        return has_permission(user_role, feature)

def check_permissions(user_role: str, required_permission: str):
    """Alias helper for permission validation."""
    PermissionService.authorize(user_role, required_permission)

from datetime import datetime, timezone, timedelta
import logging
from typing import Optional

import database
from enterprise.models import Subscription, Invoice

logger = logging.getLogger(__name__)

class SubscriptionTier:
    FOUNDER = "Founder"
    PRO = "Pro"
    TEAM = "Team"
    ENTERPRISE = "Enterprise"

# Features mapped to specific subscription levels
TIER_FEATURES = {
    SubscriptionTier.FOUNDER: {
        "view_dashboard",
        "read_reports",
        "execute_trade",
        "advanced_analytics",
        "team_collaboration",
        "shared_watchlists",
        "shared_alerts",
        "multi_org_control",
        "api_access",
        "audit_export",
        "custom_webhooks"
    },
    SubscriptionTier.ENTERPRISE: {
        "view_dashboard",
        "read_reports",
        "execute_trade",
        "advanced_analytics",
        "team_collaboration",
        "shared_watchlists",
        "shared_alerts",
        "multi_org_control",
        "api_access",
        "audit_export",
        "custom_webhooks"
    },
    SubscriptionTier.TEAM: {
        "view_dashboard",
        "read_reports",
        "execute_trade",
        "advanced_analytics",
        "team_collaboration",
        "shared_watchlists",
        "shared_alerts"
    },
    SubscriptionTier.PRO: {
        "view_dashboard",
        "read_reports",
        "execute_trade",
        "advanced_analytics"
    }
}

def create_subscription(organization_id: int, tier: str, expires_in_days: int = 30) -> dict:
    """Create or update a subscription tier for an organization."""
    session = database.get_session()
    try:
        # Check for existing subscription
        sub = session.query(Subscription).filter(Subscription.organization_id == organization_id).first()
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        if sub:
            sub.tier = tier
            sub.status = "active"
            sub.expires_at = expires_at
        else:
            sub = Subscription(
                organization_id=organization_id,
                tier=tier,
                status="active",
                expires_at=expires_at
            )
            session.add(sub)

        session.commit()
        return {
            "success": True,
            "subscription": {
                "id": sub.id,
                "organization_id": sub.organization_id,
                "tier": sub.tier,
                "status": sub.status,
                "expires_at": sub.expires_at.isoformat() if sub.expires_at else None
            }
        }
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def check_feature_gate(organization_id: int, feature: str) -> bool:
    """Check if an organization is authorized to access a feature based on subscription level."""
    session = database.get_session()
    try:
        sub = session.query(Subscription).filter(Subscription.organization_id == organization_id).first()
        if not sub or sub.status != "active":
            logger.warning("Feature Gating: organization %s has no active subscription", organization_id)
            return False

        # Expiry check
        now = datetime.now(timezone.utc)
        if sub.expires_at:
            expires_at_utc = sub.expires_at.replace(tzinfo=timezone.utc)
            if now > expires_at_utc:
                logger.warning("Feature Gating: organization %s subscription has expired", organization_id)
                return False

        features = TIER_FEATURES.get(sub.tier, set())
        return feature in features
    finally:
        session.close()

def generate_invoice(organization_id: int, subscription_id: int, amount: float) -> dict:
    """Generate a billing invoice record (payment abstraction layer)."""
    session = database.get_session()
    try:
        invoice = Invoice(
            organization_id=organization_id,
            subscription_id=subscription_id,
            amount=amount,
            status="unpaid"
        )
        session.add(invoice)
        session.commit()

        return {
            "success": True,
            "invoice": {
                "id": invoice.id,
                "organization_id": invoice.organization_id,
                "subscription_id": invoice.subscription_id,
                "amount": invoice.amount,
                "status": invoice.status,
                "created_at": invoice.created_at.isoformat() if invoice.created_at else None
            }
        }
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from database import (
    Organization,
    UserOrganizationRole,
    TeamWorkspace,
    EnterpriseAPIKey,
    EnterpriseAuditLog,
    get_session,
)

logger = logging.getLogger(__name__)


class OrganizationService:
    def __init__(self, session_factory: Optional[Callable[[], Any]] = None):
        self.session_factory = session_factory or get_session
        self.is_test = session_factory is not None

    def _org_to_dict(self, org: Organization) -> dict[str, Any]:
        return {
            "id": org.id,
            "name": org.name,
            "tenant_id": org.tenant_id,
            "status": org.status,
            "created_at": org.created_at,
        }

    def _role_to_dict(self, role: UserOrganizationRole) -> dict[str, Any]:
        return {
            "id": role.id,
            "user_id": role.user_id,
            "organization_id": role.organization_id,
            "role": role.role,
            "created_at": role.created_at,
        }

    def _workspace_to_dict(self, ws: TeamWorkspace) -> dict[str, Any]:
        return {
            "id": ws.id,
            "organization_id": ws.organization_id,
            "name": ws.name,
            "config": ws.config or {},
            "created_at": ws.created_at,
        }

    def _key_to_dict(self, key: EnterpriseAPIKey) -> dict[str, Any]:
        return {
            "id": key.id,
            "organization_id": key.organization_id,
            "name": key.name,
            "is_active": key.is_active,
            "expires_at": key.expires_at,
            "created_at": key.created_at,
        }

    def _audit_to_dict(self, log: EnterpriseAuditLog) -> dict[str, Any]:
        return {
            "id": log.id,
            "organization_id": log.organization_id,
            "user_id": log.user_id,
            "action": log.action,
            "details": log.details or {},
            "ip_address": log.ip_address,
            "created_at": log.created_at,
        }

    def create_organization(self, name: str, tenant_id: str, status: str = "ACTIVE") -> dict[str, Any]:
        session = self.session_factory()
        try:
            existing = session.query(Organization).filter(Organization.tenant_id == tenant_id).first()
            if existing:
                raise ValueError(f"Organization with tenant ID '{tenant_id}' already exists.")

            org = Organization(name=name, tenant_id=tenant_id, status=status)
            session.add(org)
            if not self.is_test:
                session.commit()
                session.refresh(org)
            else:
                session.flush()

            logger.info("TELEMETRY: [OrganizationService] Created organization '%s' (ID: %s)", name, org.id)
            return self._org_to_dict(org)
        except Exception as e:
            if not self.is_test:
                session.rollback()
            logger.error("Failed to create organization '%s': %s", name, e)
            raise
        finally:
            if not self.is_test:
                session.close()

    def get_organization(self, organization_id: int) -> Optional[dict[str, Any]]:
        session = self.session_factory()
        try:
            org = session.query(Organization).filter(Organization.id == organization_id).first()
            if not org:
                return None
            return self._org_to_dict(org)
        finally:
            if not self.is_test:
                session.close()

    def get_organization_by_tenant(self, tenant_id: str) -> Optional[dict[str, Any]]:
        session = self.session_factory()
        try:
            org = session.query(Organization).filter(Organization.tenant_id == tenant_id).first()
            if not org:
                return None
            return self._org_to_dict(org)
        finally:
            if not self.is_test:
                session.close()

    def assign_user_role(self, user_id: int, organization_id: int, role: str) -> dict[str, Any]:
        session = self.session_factory()
        try:
            org = session.query(Organization).filter(Organization.id == organization_id).first()
            if not org:
                raise ValueError(f"Organization {organization_id} does not exist.")

            role_record = (
                session.query(UserOrganizationRole)
                .filter(
                    UserOrganizationRole.user_id == user_id,
                    UserOrganizationRole.organization_id == organization_id,
                )
                .first()
            )

            if role_record:
                role_record.role = role
            else:
                role_record = UserOrganizationRole(
                    user_id=user_id, organization_id=organization_id, role=role
                )
                session.add(role_record)

            if not self.is_test:
                session.commit()
                session.refresh(role_record)
            else:
                session.flush()

            logger.info(
                "TELEMETRY: [OrganizationService] Assigned user %s role '%s' in organization %s",
                user_id,
                role,
                organization_id,
            )
            return self._role_to_dict(role_record)
        except Exception as e:
            if not self.is_test:
                session.rollback()
            logger.error("Failed to assign role to user %s: %s", user_id, e)
            raise
        finally:
            if not self.is_test:
                session.close()

    def get_user_role(self, user_id: int, organization_id: int) -> Optional[str]:
        session = self.session_factory()
        try:
            role_record = (
                session.query(UserOrganizationRole)
                .filter(
                    UserOrganizationRole.user_id == user_id,
                    UserOrganizationRole.organization_id == organization_id,
                )
                .first()
            )
            return role_record.role if role_record else None
        finally:
            if not self.is_test:
                session.close()

    def create_workspace(self, organization_id: int, name: str, config: Optional[dict] = None) -> dict[str, Any]:
        session = self.session_factory()
        try:
            org = session.query(Organization).filter(Organization.id == organization_id).first()
            if not org:
                raise ValueError(f"Organization {organization_id} does not exist.")

            workspace = TeamWorkspace(
                organization_id=organization_id, name=name, config=config or {}
            )
            session.add(workspace)
            if not self.is_test:
                session.commit()
                session.refresh(workspace)
            else:
                session.flush()

            logger.info(
                "TELEMETRY: [OrganizationService] Created workspace '%s' in organization %s",
                name,
                organization_id,
            )
            return self._workspace_to_dict(workspace)
        except Exception as e:
            if not self.is_test:
                session.rollback()
            logger.error("Failed to create workspace '%s': %s", name, e)
            raise
        finally:
            if not self.is_test:
                session.close()

    def get_workspaces(self, organization_id: int) -> list[dict[str, Any]]:
        session = self.session_factory()
        try:
            workspaces = (
                session.query(TeamWorkspace)
                .filter(TeamWorkspace.organization_id == organization_id)
                .all()
            )
            return [self._workspace_to_dict(ws) for ws in workspaces]
        finally:
            if not self.is_test:
                session.close()

    def generate_api_key(
        self, organization_id: int, name: str, expires_in_days: Optional[int] = None
    ) -> tuple[str, dict[str, Any]]:
        session = self.session_factory()
        try:
            org = session.query(Organization).filter(Organization.id == organization_id).first()
            if not org:
                raise ValueError(f"Organization {organization_id} does not exist.")

            # Generate random secure token prefix with raw entropy
            raw_token = f"nx_{secrets.token_urlsafe(32)}"
            key_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

            expires_at = None
            if expires_in_days is not None:
                expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
                # Store as naive UTC in DB for compatibility
                expires_at = expires_at.replace(tzinfo=None)

            api_key_rec = EnterpriseAPIKey(
                organization_id=organization_id,
                key_hash=key_hash,
                name=name,
                is_active=True,
                expires_at=expires_at,
            )
            session.add(api_key_rec)
            if not self.is_test:
                session.commit()
                session.refresh(api_key_rec)
            else:
                session.flush()

            logger.info(
                "TELEMETRY: [OrganizationService] Generated API key '%s' for organization %s",
                name,
                organization_id,
            )
            return raw_token, self._key_to_dict(api_key_rec)
        except Exception as e:
            if not self.is_test:
                session.rollback()
            logger.error("Failed to generate API key: %s", e)
            raise
        finally:
            if not self.is_test:
                session.close()

    def authenticate_api_key(self, raw_key: str) -> Optional[dict[str, Any]]:
        session = self.session_factory()
        try:
            key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
            api_key_rec = session.query(EnterpriseAPIKey).filter(EnterpriseAPIKey.key_hash == key_hash).first()
            if not api_key_rec:
                return None

            if not api_key_rec.is_active:
                return None

            if api_key_rec.expires_at:
                now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
                if api_key_rec.expires_at < now_utc:
                    return None

            # Retrieve associated organization
            org = session.query(Organization).filter(Organization.id == api_key_rec.organization_id).first()
            if not org or org.status != "ACTIVE":
                return None

            return self._org_to_dict(org)
        finally:
            if not self.is_test:
                session.close()

    def log_audit_action(
        self,
        organization_id: int,
        action: str,
        user_id: Optional[int] = None,
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> dict[str, Any]:
        session = self.session_factory()
        try:
            audit = EnterpriseAuditLog(
                organization_id=organization_id,
                user_id=user_id,
                action=action,
                details=details or {},
                ip_address=ip_address,
            )
            session.add(audit)
            if not self.is_test:
                session.commit()
                session.refresh(audit)
            else:
                session.flush()

            logger.info(
                "TELEMETRY: [AuditLog] Captured action '%s' for organization %s",
                action,
                organization_id,
            )
            return self._audit_to_dict(audit)
        except Exception as e:
            if not self.is_test:
                session.rollback()
            logger.error("Failed to write audit log: %s", e)
            raise
        finally:
            if not self.is_test:
                session.close()

    def get_audit_logs(self, organization_id: int) -> list[dict[str, Any]]:
        session = self.session_factory()
        try:
            logs = (
                session.query(EnterpriseAuditLog)
                .filter(EnterpriseAuditLog.organization_id == organization_id)
                .order_by(EnterpriseAuditLog.created_at.desc())
                .all()
            )
            return [self._audit_to_dict(log) for log in logs]
        finally:
            if not self.is_test:
                session.close()

import secrets
from datetime import datetime, timedelta, timezone
import logging

import database
from database import User
from enterprise.models import Organization, Team, OrganizationMember, TeamInvitation

logger = logging.getLogger(__name__)

def create_organization(name: str, user_id: int) -> dict:
    session = database.get_session()
    try:
        org = Organization(name=name)
        session.add(org)
        session.commit()

        # Add the creator as the Founder of this organization
        member = OrganizationMember(
            organization_id=org.id,
            user_id=user_id,
            role="Founder"
        )
        session.add(member)
        session.commit()

        return {
            "success": True,
            "organization": {
                "id": org.id,
                "name": org.name,
                "created_at": org.created_at.isoformat() if org.created_at else None
            }
        }
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def create_team(organization_id: int, name: str) -> dict:
    session = database.get_session()
    try:
        team = Team(organization_id=organization_id, name=name)
        session.add(team)
        session.commit()

        return {
            "success": True,
            "team": {
                "id": team.id,
                "organization_id": team.organization_id,
                "name": team.name,
                "created_at": team.created_at.isoformat() if team.created_at else None
            }
        }
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def add_organization_member(organization_id: int, user_id: int, role: str) -> dict:
    session = database.get_session()
    try:
        # Check if already a member
        existing = session.query(OrganizationMember).filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id
        ).first()
        if existing:
            existing.role = role
            session.commit()
            return {"success": True, "message": "Membership role updated"}

        member = OrganizationMember(
            organization_id=organization_id,
            user_id=user_id,
            role=role
        )
        session.add(member)
        session.commit()
        return {"success": True, "message": "Member added successfully"}
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def send_team_invitation(organization_id: int, email: str, role: str, team_id: int = None) -> dict:
    session = database.get_session()
    try:
        token = secrets.token_hex(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        invitation = TeamInvitation(
            organization_id=organization_id,
            team_id=team_id,
            email=email,
            role=role,
            token=token,
            is_accepted=False,
            expires_at=expires_at
        )
        session.add(invitation)
        session.commit()

        return {
            "success": True,
            "invitation": {
                "id": invitation.id,
                "organization_id": invitation.organization_id,
                "team_id": invitation.team_id,
                "email": invitation.email,
                "role": invitation.role,
                "token": invitation.token,
                "is_accepted": invitation.is_accepted,
                "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None
            }
        }
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def accept_team_invitation(token: str, user_id: int) -> dict:
    session = database.get_session()
    try:
        invitation = session.query(TeamInvitation).filter(
            TeamInvitation.token == token,
            TeamInvitation.is_accepted == False
        ).first()

        if not invitation:
            return {"success": False, "error": "Invalid or already accepted invitation token"}

        now = datetime.now(timezone.utc)
        expires_at_utc = invitation.expires_at.replace(tzinfo=timezone.utc) if invitation.expires_at else now
        if now > expires_at_utc:
            return {"success": False, "error": "Invitation token has expired"}

        # Accept invitation
        invitation.is_accepted = True
        session.commit()

        # Add user to organization members
        member_res = add_organization_member(invitation.organization_id, user_id, invitation.role)
        if not member_res["success"]:
            return member_res

        return {"success": True, "message": "Invitation accepted, user added to organization"}
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def get_organization_members(organization_id: int) -> list:
    session = database.get_session()
    try:
        members = session.query(OrganizationMember).filter(
            OrganizationMember.organization_id == organization_id
        ).all()
        return [
            {
                "id": m.id,
                "organization_id": m.organization_id,
                "user_id": m.user_id,
                "role": m.role,
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in members
        ]
    finally:
        session.close()

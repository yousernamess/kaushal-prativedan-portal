"""Users router — admin user management, invitations."""

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, hash_password, require_admin
from app.core.config import get_settings
from app.core.database import get_db
from app.models import Invitation, User, UserRole
from app.schemas import (
    AcceptInvitationRequest,
    InviteRequest,
    InvitationRead,
    UserRead,
    UserUpdateRequest,
)

settings = get_settings()
router = APIRouter(prefix="/users", tags=["Users"])


# ── Admin: List users ──────────────────────────────────────────────


@router.get("", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return db.query(User).order_by(User.created_at.desc()).all()


# ── Admin: Update user (activate/deactivate, change role) ─────────


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == current_user.id:
        raise HTTPException(400, "Cannot modify your own account")

    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.role is not None:
        if payload.role not in ("admin", "user"):
            raise HTTPException(422, "Role must be 'admin' or 'user'")
        user.role = UserRole(payload.role)

    db.commit()
    db.refresh(user)
    return user


# ── Admin: Invite user ─────────────────────────────────────────────


@router.post("/invite", response_model=InvitationRead, status_code=status.HTTP_201_CREATED)
def invite_user(
    payload: InviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    # Check if user already exists
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(409, "A user with this email already exists")

    # Check for pending invitation
    pending = (
        db.query(Invitation)
        .filter(
            Invitation.email == payload.email,
            Invitation.is_used == False,
            Invitation.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )
    if pending:
        raise HTTPException(409, "An active invitation already exists for this email")

    if payload.role not in ("admin", "user"):
        raise HTTPException(422, "Role must be 'admin' or 'user'")

    token = secrets.token_urlsafe(32)
    invitation = Invitation(
        email=payload.email,
        token=token,
        role=UserRole(payload.role),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        invited_by_id=current_user.id,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


# ── Admin: List invitations ────────────────────────────────────────


@router.get("/invitations", response_model=list[InvitationRead])
def list_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return db.query(Invitation).order_by(Invitation.created_at.desc()).all()


# ── Public: Accept invitation ──────────────────────────────────────


@router.post("/accept-invitation", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def accept_invitation(payload: AcceptInvitationRequest, db: Session = Depends(get_db)):
    invitation = db.query(Invitation).filter(Invitation.token == payload.token).first()
    if not invitation:
        raise HTTPException(400, "Invalid invitation link")
    if invitation.is_used:
        raise HTTPException(400, "This invitation has already been used")
    if invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(400, "This invitation has expired")

    # Check user doesn't already exist
    existing = db.query(User).filter(User.email == invitation.email).first()
    if existing:
        raise HTTPException(409, "An account with this email already exists")

    user = User(
        email=invitation.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=invitation.role,
        is_active=True,
    )
    db.add(user)
    invitation.is_used = True
    db.commit()
    db.refresh(user)
    return user


# ── Public: Get invitation info (for the invite link page) ─────────


@router.get("/invitation-info/{token}")
def invitation_info(token: str, db: Session = Depends(get_db)):
    invitation = db.query(Invitation).filter(Invitation.token == token).first()
    if not invitation:
        raise HTTPException(404, "Invalid invitation link")
    if invitation.is_used:
        raise HTTPException(400, "This invitation has already been used")
    if invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(400, "This invitation has expired")
    return {"email": invitation.email, "role": invitation.role.value}

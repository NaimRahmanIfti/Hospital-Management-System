# app/core/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import decode_access_token
from app.models.user import User


# ── OAuth2 Scheme ─────────────────────────────────────────────────
# OAuth2PasswordBearer tells FastAPI:
#   "Tokens come in the Authorization header as: Bearer eyJhbGci..."
#   "If there's no token, return 401 automatically"
#
# tokenUrl="/auth/login" → tells the /docs UI where to log in
# (the interactive docs will show a "Authorize" button pointing here)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Core dependency: get current user from token ──────────────────
# This function is the heart of auth. Every protected route calls this.
#
# FastAPI's Depends() system works like this:
#   When a route has:  current_user: User = Depends(get_current_user)
#   FastAPI sees it, calls get_current_user() automatically,
#   and passes the result as current_user to your route function.
#   If this function raises HTTPException, the route never runs.

def get_current_user(
    token: str = Depends(oauth2_scheme),   # FastAPI extracts token from header
    db: Session = Depends(get_db)          # FastAPI gives us a DB session
) -> User:
    """
    Extract the user from the JWT token.
    Raises 401 if token is missing, expired, or tampered.
    """
    # We'll raise this specific exception if anything goes wrong
    # WWW-Authenticate header is part of the OAuth2 spec
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Step 1: Decode and verify the JWT
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    # Step 2: Extract user_id from the "sub" claim
    # "sub" is a standard JWT claim meaning "subject" (who this token is about)
    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise credentials_exception

    # Step 3: Load the actual user from DB
    # Why hit the DB? Because the user might have been deactivated
    # since the token was issued — tokens don't self-invalidate
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Extends get_current_user — also checks the user is active.
    Use this on most routes (not just logged in, but not banned either).
    """
    if current_user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    return current_user


# ── Role-based dependencies ───────────────────────────────────────
# These let you restrict routes to specific roles.
# Usage in a route:
#   @router.get("/admin-only")
#   def admin_route(admin = Depends(require_admin)):
#       ...

def _role_name(role: object) -> str:
    if isinstance(role, str):
        return role
    value = getattr(role, "value", None)
    if isinstance(value, str):
        return value
    return str(role)


def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    if _role_name(current_user.role) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def require_doctor(
    current_user: User = Depends(get_current_active_user)
) -> User:
    if _role_name(current_user.role) not in ("doctor", "admin"):
        # Admins can always do what doctors can do
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor access required"
        )
    return current_user


def require_patient(
    current_user: User = Depends(get_current_active_user)
) -> User:
    if _role_name(current_user.role) not in ("patient", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient access required"
        )
    return current_user
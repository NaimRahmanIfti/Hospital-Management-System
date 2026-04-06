# app/routers/users.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.core.db import get_db
from app.core.dependencies import get_current_active_user, require_admin
from app.schemas.user import UserResponse, UserUpdate
from app.services import user_service
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])


# ── GET /users (admin only) ───────────────────────────────────────
@router.get("/", response_model=List[UserResponse])
def list_users(
    skip: int = 0,                             # pagination: how many to skip
    limit: int = 20,                           # pagination: max to return
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),          # _ = we need the check, not the value
):
    """
    List all users. Admin only.
    Use skip/limit for pagination: skip=20&limit=20 → page 2.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


# ── GET /users/{user_id} ──────────────────────────────────────────
@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a user by ID.
    Users can only see their own profile; admins can see anyone.
    """
    # Authorization check inside the route
    # (not a dependency because logic depends on the path parameter)
    current_role = getattr(current_user.role, "value", current_user.role)
    is_admin = bool(current_role == "admin")
    is_owner = bool(current_user.id == user_id)
    if not is_admin and not is_owner:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
        )
    return user_service.get_user_by_id(db, user_id)


# ── PATCH /users/{user_id} ────────────────────────────────────────
# PATCH = partial update (only send fields you want to change)
# PUT   = full replace  (send the entire object)
# We use PATCH — it's more practical for profile edits
@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update a user profile (partial).
    Users can only update their own profile; admins can update anyone.
    """
    current_role = getattr(current_user.role, "value", current_user.role)
    is_admin = bool(current_role == "admin")
    is_owner = bool(current_user.id == user_id)
    if not is_admin and not is_owner:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )
    return user_service.update_user(db, user_id, data)


# ── DELETE /users/{user_id} (soft delete) ────────────────────────
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """
    Deactivate (soft-delete) a user. Admin only.
    Sets is_active=False — does NOT delete the row.
    204 = success with no response body.
    """
    user_service.deactivate_user(db, user_id)
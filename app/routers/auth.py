# app/routers/auth.py

from typing import cast

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import create_access_token
from app.core.dependencies import get_current_active_user, get_user_service
from app.schemas.user import UserCreate, UserResponse, Token
from app.services.user_service import UserService
from app.models.user import User


# APIRouter is like a mini FastAPI app — it groups related routes.
# prefix="/auth" means all routes here start with /auth
# tags=["Auth"] groups them together in the /docs UI
router = APIRouter(prefix="/auth", tags=["Auth"])


# ── POST /auth/register ───────────────────────────────────────────
@router.post(
    "/register",
    response_model=UserResponse,           # Pydantic will filter the response through this
    status_code=status.HTTP_201_CREATED,   # 201 = resource created (not 200)
)
def register(
    data: UserCreate,                      # Pydantic validates the request body
    user_service: UserService = Depends(get_user_service),         # FastAPI injects a DB session
):
    """
    Register a new user.

    - Validates email format + password strength (schema)
    - Checks email isn't already taken (service)
    - Hashes password (service)
    - Returns the new user WITHOUT the password (response_model)
    """
    user = user_service.create(data)
    return user


# ── POST /auth/login ──────────────────────────────────────────────
# OAuth2PasswordRequestForm is a special FastAPI form that expects:
#   Content-Type: application/x-www-form-urlencoded
#   Fields: username (we treat as email) + password
#
# WHY form data instead of JSON?
# OAuth2 spec requires form data for the token endpoint.
# This makes /docs "Authorize" button work out of the box.
@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service),
):
    """
    Login and receive a JWT access token.

    Send as form data:
        username = your@email.com
        password = YourPassword1

    Returns: { access_token: "eyJ...", token_type: "bearer" }
    """
    # OAuth2PasswordRequestForm uses "username" field — we use it as email
    user = user_service.authenticate(form_data.username, form_data.password)

    # Build the JWT payload
    # "sub" (subject) is the standard JWT claim for the user identifier
    # We store both id and role so we don't need a DB call for role checks
    token = create_access_token(data={
        "sub": str(user.id),
        "role": user.role.value,
    })

    return Token(access_token=token)


# ── GET /auth/me ──────────────────────────────────────────────────
# Depends(get_current_active_user) → FastAPI automatically:
#   1. Extracts the Bearer token from the Authorization header
#   2. Decodes and validates the JWT
#   3. Loads the user from DB
#   4. Passes the User object as current_user
#   If any step fails → 401 returned, this function never runs
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    """
    Get the currently logged-in user's profile.
    Requires: Authorization: Bearer <token>
    """
    return current_user


# ── GET /auth/me/role ─────────────────────────────────────────────
@router.get("/me/role")
def get_my_role(current_user: User = Depends(get_current_active_user)) -> dict[str, int | str]:
    """Quick endpoint to check your role — useful for frontend routing."""
    return {
        "user_id": cast(int, current_user.id),
        "email": str(current_user.email),
        "role": str(current_user.role.value),
    }
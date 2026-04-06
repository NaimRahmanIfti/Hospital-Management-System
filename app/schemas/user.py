# app/schemas/user.py

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from app.models.user import UserRole


# ── Base ──────────────────────────────────────────────────────────
# Fields shared by ALL user schemas.
# We never instantiate this directly — it's a parent class.
class UserBase(BaseModel):
    email: EmailStr                  # EmailStr validates format: "a@b.com" ✅  "notanemail" ❌
    full_name: str = Field(
        ...,                         # "..." means REQUIRED (no default)
        min_length=2,
        max_length=100,
        examples=["Jane Smith"],
    )
    role: UserRole = UserRole.patient  # default role is patient


# ── Create ────────────────────────────────────────────────────────
# Used when registering a new user.
# Adds 'password' — but only for input, never for output.
class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

    # field_validator lets you add custom validation logic.
    # This runs AFTER pydantic checks the type.
    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        # Basic strength check — real systems would be stricter
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v


# ── Update ────────────────────────────────────────────────────────
# Used when editing a user profile.
# ALL fields are Optional — user only sends what they want to change.
# Optional[str] = None means "this field may be absent or None"
class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    password:  Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None


# ── Response ──────────────────────────────────────────────────────
# What the API sends BACK to the client.
# Notice: NO password or hashed_password field here.
# Even if it's in the DB row, Pydantic won't include fields
# that aren't defined in this schema.
class UserResponse(UserBase):
    id: int
    is_active: bool

    # model_config tells Pydantic: "accept SQLAlchemy model objects"
    # Without this, Pydantic only accepts plain dicts.
    # from_attributes=True enables: UserResponse.model_validate(db_user_object)
    model_config = {"from_attributes": True}


# ── Token schemas (for JWT login) ────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"   # standard OAuth2 convention

class TokenData(BaseModel):
    # This is what we store INSIDE the JWT token
    # We only store the user_id — minimal data in token is best practice
    user_id: Optional[int] = None
    role: Optional[str] = None
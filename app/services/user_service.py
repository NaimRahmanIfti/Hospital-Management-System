# app/services/user_service.py

from typing import cast

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password


def get_user_by_id(db: Session, user_id: int) -> User:
    """
    Fetch a user by ID. Raises 404 if not found.
    We raise the HTTP exception here in the service so every
    caller gets consistent error handling — not scattered across routes.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    Fetch a user by email. Returns None if not found (no exception).
    Used during login — we handle "not found" differently there.
    """
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, data: UserCreate) -> User:
    """
    Register a new user.

    Steps:
    1. Check email not already taken
    2. Hash the password (NEVER store plain text)
    3. Create the DB row
    4. Commit + refresh (refresh loads the auto-assigned id back into the object)
    """
    # Step 1: duplicate check
    existing = get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists"
        )

    # Step 2: hash password
    # data.password is the plain text from the request
    # We never touch it again after this line
    hashed = hash_password(data.password)

    # Step 3: build the DB model
    # model_dump() converts the Pydantic schema to a dict
    # exclude={"password"} drops the plain password field
    # We manually add hashed_password instead
    user = User(
        **data.model_dump(exclude={"password"}),
        hashed_password=hashed,
    )

    # Step 4: save to DB
    db.add(user)       # stage the INSERT
    db.commit()        # write to PostgreSQL
    db.refresh(user)   # re-read from DB → populates user.id, defaults, etc.

    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Verify email + password for login.
    Returns the user if credentials are valid.
    Raises 401 if anything is wrong.

    WHY same error for "user not found" and "wrong password"?
    If we said "user not found" an attacker knows that email
    isn't registered. Vague errors reveal less information.
    """
    user = get_user_by_email(db, email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    hashed_password = cast(str, user.hashed_password)

    if not verify_password(password, hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not cast(bool, user.is_active):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    return user


def update_user(db: Session, user_id: int, data: UserUpdate) -> User:
    """
    Partial update — only change fields the client actually sent.
    model_dump(exclude_unset=True) returns ONLY the fields present
    in the request body, not fields with default values.
    """
    user = get_user_by_id(db, user_id)

    # exclude_unset=True is the key to partial updates
    # If client sends { "full_name": "Jane" }, we only update full_name
    # NOT every other field (which would overwrite with None)
    updates = data.model_dump(exclude_unset=True)

    # Handle password separately — it needs hashing
    if "password" in updates:
        updates["hashed_password"] = hash_password(updates.pop("password"))

    for field, value in updates.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user_id: int) -> User:
    """
    Soft delete — set is_active=False instead of deleting the row.
    WHY? Hard deletes break foreign keys (appointments still reference this user).
    Soft deletes preserve data integrity and audit history.
    """
    user = get_user_by_id(db, user_id)
    setattr(user, "is_active", False)
    db.commit()
    db.refresh(user)
    return user
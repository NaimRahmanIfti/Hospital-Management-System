# app/core/security.py

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings


# ── Password Hashing ──────────────────────────────────────────────
# CryptContext is passlib's abstraction over hashing algorithms.
# schemes=["bcrypt"] → use bcrypt (the industry standard for passwords)
# deprecated="auto"  → if we ever switch algorithms, old hashes still work
#
# WHY bcrypt over md5/sha256?
#   md5("Secret123") always = same output → rainbow table attacks work
#   bcrypt adds a random "salt" each time:
#     hash("Secret123") → "$2b$12$RANDOM_SALT...HASH"
#     hash("Secret123") → "$2b$12$DIFFERENT_SALT...DIFFERENT_HASH"
#   Two identical passwords produce different hashes → rainbow tables useless
#   Also: bcrypt is intentionally SLOW (12 rounds) → brute force takes years
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Turn a plain text password into a bcrypt hash.
    Called once during registration — result stored in DB.

    "Secret123"  →  "$2b$12$abc123...xyz"
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain password matches the stored hash.
    Called every time a user logs in.

    bcrypt extracts the salt from the hash, re-hashes the input,
    then compares — so two different hashes of the same password
    both verify correctly.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ── JWT Tokens ────────────────────────────────────────────────────
# JWT = JSON Web Token
# Structure: HEADER.PAYLOAD.SIGNATURE (three base64 parts, dot-separated)
#
# HEADER:    { "alg": "HS256", "typ": "JWT" }
# PAYLOAD:   { "sub": "1", "role": "doctor", "exp": 1234567890 }
# SIGNATURE: HMAC_SHA256(header + payload, SECRET_KEY)
#
# The signature is the key part — only our server knows SECRET_KEY.
# If anyone tampers with the payload, the signature won't match → rejected.
# The client can READ the payload (it's just base64) but can't MODIFY it.


def create_access_token(
    data: Mapping[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a signed JWT token.

    data: what to store inside the token, e.g. {"sub": "1", "role": "doctor"}
    expires_delta: how long until the token expires

    Returns: signed JWT string like "eyJhbGci..."
    """
    # Make a copy so we don't mutate the caller's dict
    payload: dict[str, Any] = dict(data)

    # Set expiry time
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # "exp" is a standard JWT claim — jose validates it automatically
    # "sub" (subject) is the standard claim for the user identifier
    payload.update({"exp": expire})

    # jwt.encode() creates the signed token string
    # algorithm HS256 = HMAC + SHA-256 (symmetric — same key to sign and verify)
    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return token


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """
    Verify and decode a JWT token.

    Returns the payload dict if valid, None if invalid/expired.

    jose automatically checks:
      - Signature (was this signed with our SECRET_KEY?)
      - Expiry   (is "exp" in the past?)
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        # JWTError covers: expired, tampered, malformed
        return None
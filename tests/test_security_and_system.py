# tests/test_security_and_system.py
#
# UNIT tests: they call plain Python functions directly, with no HTTP and no database.
# They are the fastest kind of test. Use them for pure logic like hashing and tokens.

from datetime import timedelta

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_is_not_the_password_and_verifies():
    hashed = hash_password("Secret123")
    assert hashed != "Secret123"
    assert hashed.startswith("$2b$")               # bcrypt format
    assert verify_password("Secret123", hashed)
    assert not verify_password("secret123", hashed)  # case matters


def test_same_password_hashes_differently_each_time():
    # bcrypt adds a random "salt", so two users with the same password
    # get different hashes, and precomputed "rainbow tables" don't work.
    assert hash_password("Secret123") != hash_password("Secret123")


def test_token_roundtrip():
    token = create_access_token({"sub": "42", "role": "doctor"})
    payload = decode_access_token(token)
    assert payload["sub"] == "42" and payload["role"] == "doctor"
    assert "exp" in payload                         # every token has an expiry


def test_expired_token_is_rejected():
    token = create_access_token({"sub": "42"}, expires_delta=timedelta(seconds=-1))
    assert decode_access_token(token) is None


def test_tampered_token_is_rejected():
    token = create_access_token({"sub": "42"})
    header, payload, signature = token.split(".")
    tampered = f"{header}.{payload}.{signature[:-2]}xx"
    assert decode_access_token(tampered) is None


# ── System endpoints ─────────────────────────────────────────────
def test_health_and_root(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").json()["docs"] == "/docs"


def test_openapi_docs_list_every_router(client):
    paths = client.get("/openapi.json").json()["paths"]
    for prefix in ["/auth", "/users", "/patients", "/doctors", "/appointments",
                   "/medical-records", "/invoices", "/documents"]:
        assert any(p.startswith(prefix) for p in paths), f"{prefix} missing from API"

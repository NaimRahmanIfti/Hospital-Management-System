# tests/test_auth.py
#
# Register, log in, and the JWT that protects every other endpoint.
# Pattern for every test: ARRANGE (set up) → ACT (call the API) → ASSERT (check).

import pytest

from tests.conftest import PASSWORD, login, make_user, unique_email


def register(client, **overrides):
    body = {"email": unique_email("p"), "full_name": "Jane Smith", "password": PASSWORD}
    body.update(overrides)
    return client.post("/auth/register", json=body)


def test_register_returns_user_without_password(client):
    r = register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["role"] == "patient"          # default role
    assert "password" not in body
    assert "hashed_password" not in body      # the hash must never leave the server


def test_register_patient_creates_patient_profile(client):
    user = make_user(client, "patient")
    r = client.get("/patients/my", headers=user.headers)
    assert r.status_code == 200
    assert r.json()["user_id"] == user.id


def test_duplicate_email_is_rejected(client):
    email = unique_email("dup")
    assert register(client, email=email).status_code == 201
    r = register(client, email=email)
    assert r.status_code in (400, 409)


# parametrize = run the SAME test once per input row. 4 rows → 4 tests.
@pytest.mark.parametrize(
    "password",
    ["short1A",          # < 8 characters
     "nouppercase1",     # no uppercase letter
     "NoNumbersHere"],   # no digit
)
def test_weak_passwords_are_rejected(client, password):
    assert register(client, password=password).status_code == 422


def test_invalid_email_is_rejected(client):
    assert register(client, email="not-an-email").status_code == 422


def test_login_returns_bearer_token(client):
    user = make_user(client)
    r = client.post("/auth/login", data={"username": user.email, "password": PASSWORD})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"].count(".") == 2   # a JWT is header.payload.signature


def test_wrong_password_and_unknown_email_give_same_error(client):
    # Same message for both → an attacker can't discover which emails exist.
    user = make_user(client)
    wrong_pw = client.post("/auth/login", data={"username": user.email, "password": "Wrong1234"})
    no_user = client.post("/auth/login", data={"username": "ghost@test.com", "password": "Wrong1234"})
    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.json()["detail"] == no_user.json()["detail"]


def test_me_returns_current_user(client):
    user = make_user(client, "doctor")
    r = client.get("/auth/me", headers=user.headers)
    assert r.status_code == 200
    assert r.json()["email"] == user.email
    assert client.get("/auth/me/role", headers=user.headers).json()["role"] == "doctor"


@pytest.mark.parametrize(
    "headers",
    [{},                                                  # no token at all
     {"Authorization": "Bearer not.a.real-token"},        # garbage token
     {"Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.forged"}],  # bad signature
)
def test_protected_endpoint_rejects_missing_or_bad_token(client, headers):
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_deactivated_user_cannot_log_in_or_use_old_token(client, admin):
    user = make_user(client)
    assert client.delete(f"/users/{user.id}", headers=admin.headers).status_code == 204

    # The token issued BEFORE deactivation must stop working too.
    # (That's why get_current_user re-loads the user from the DB on every request.)
    assert client.get("/auth/me", headers=user.headers).status_code == 403
    r = client.post("/auth/login", data={"username": user.email, "password": PASSWORD})
    assert r.status_code in (401, 403)


@pytest.mark.xfail(
    strict=True,
    reason="KNOWN SECURITY BUG: /auth/register accepts role='admin' from anyone. "
           "Fix it, then delete this xfail marker.",
)
def test_public_registration_cannot_create_admin(client):
    r = register(client, role="admin")
    assert r.status_code in (400, 403, 422)


def test_login_token_works_for_new_login(client):
    user = make_user(client)
    assert client.get("/auth/me", headers=login(client, user.email)).status_code == 200

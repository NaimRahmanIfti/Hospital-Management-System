# tests/conftest.py
#
# pytest loads this file automatically before any test file.
#
# Two building blocks live here:
#   FIXTURES  → reusable setup. A test asks for one by naming it as an argument:
#                 def test_x(client, admin): ...   ← pytest creates both and passes them in
#   HELPERS   → plain functions tests call to build data (users, doctors, ...)
#
# Every test talks to the app the same way the React frontend does:
# over HTTP, with a JWT in the Authorization header. That makes these
# "integration tests": router + service + model + database all run for real.

import os
import tempfile

# ── 1. Configure the app BEFORE importing it ──────────────────────
# Settings are read when the app is imported, so env vars must be set first.
# Each test run gets a fresh, throwaway SQLite database and upload folder.
# (Production uses PostgreSQL; SQLAlchemy lets the same code run on both.)
_tmp = tempfile.mkdtemp(prefix="hms-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["STORAGE_BACKEND"] = "local"
os.environ["LOCAL_STORAGE_DIR"] = f"{_tmp}/uploads"
# Fake AWS credentials: boto3 can never reach a real AWS account from tests.
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "us-west-1"

import uuid  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from datetime import datetime, timedelta  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

PASSWORD = "Password123"
PDF_BYTES = b"%PDF-1.4\n%fake test pdf\n"


# ── 2. The test client ────────────────────────────────────────────
@pytest.fixture
def client():
    # TestClient runs the FastAPI app in-process: no server, no network.
    # client.get("/health") calls the route function directly.
    with TestClient(app) as c:
        yield c
    # Undo any dependency swaps a test made (e.g. fake S3 storage).
    app.dependency_overrides.clear()


# ── 3. A logged-in user, bundled together ────────────────────────
@dataclass
class TestUser:
    __test__ = False   # tells pytest "this is not a test class" (its name starts with Test)
    id: int
    email: str
    role: str
    headers: dict      # {"Authorization": "Bearer eyJ..."}
    patient_id: int | None = None
    doctor_id: int | None = None


def unique_email(role: str) -> str:
    # uuid makes every email different, so tests never collide with each other
    return f"{role}-{uuid.uuid4().hex[:8]}@test.com"


def login(client, email: str, password: str = PASSWORD) -> dict:
    # OAuth2 login uses FORM data (data=...), not JSON (json=...)
    r = client.post("/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def make_user(client, role: str = "patient") -> TestUser:
    """Register + log in a user. Patients get their profile automatically."""
    email = unique_email(role)
    r = client.post(
        "/auth/register",
        json={"email": email, "full_name": f"Test {role.title()}", "password": PASSWORD, "role": role},
    )
    assert r.status_code == 201, r.text
    user = TestUser(id=r.json()["id"], email=email, role=role, headers=login(client, email))
    if role == "patient":
        user.patient_id = client.get("/patients/my", headers=user.headers).json()["id"]
    return user


def make_doctor(client, specialization: str = "Cardiology") -> TestUser:
    """Register a doctor user AND create their doctor profile."""
    user = make_user(client, "doctor")
    r = client.post(
        "/doctors/",
        headers=user.headers,
        json={
            "user_id": user.id,
            "specialization": specialization,
            "license_number": f"LIC-{uuid.uuid4().hex[:8]}",
            "consultation_fee": "150.00",
        },
    )
    assert r.status_code == 201, r.text
    user.doctor_id = r.json()["id"]
    return user


def future(days: int = 1, hour: int = 10) -> str:
    """An ISO datetime string in the future (appointments can't be in the past)."""
    when = (datetime.now() + timedelta(days=days)).replace(hour=hour, minute=0, second=0, microsecond=0)
    return when.isoformat()


def book(client, booker: TestUser, patient_id: int, doctor_id: int, when: str | None = None):
    return client.post(
        "/appointments/",
        headers=booker.headers,
        json={"patient_id": patient_id, "doctor_id": doctor_id, "scheduled_at": when or future(), "reason": "Checkup"},
    )


# ── 4. Ready-made fixtures for the common roles ───────────────────
@pytest.fixture
def patient(client) -> TestUser:
    return make_user(client, "patient")


@pytest.fixture
def other_patient(client) -> TestUser:
    return make_user(client, "patient")


@pytest.fixture
def doctor(client) -> TestUser:
    return make_doctor(client)


@pytest.fixture
def admin(client) -> TestUser:
    return make_user(client, "admin")


# Kept for tests/test_documents.py
def register_and_login(client, role="patient"):
    return make_user(client, role).headers


def my_patient_id(client, headers):
    r = client.get("/patients/my", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["id"]

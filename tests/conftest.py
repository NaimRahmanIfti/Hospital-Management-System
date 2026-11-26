# tests/conftest.py
#
# pytest loads this file automatically before any test.
# "Fixtures" defined here are reusable setup pieces a test asks for by name:
#   def test_something(client): ...   ← pytest passes the `client` fixture in

import os
import tempfile

# Configure the app BEFORE importing it: settings are read at import time.
# Each test run gets a throwaway SQLite DB and upload folder.
_tmp = tempfile.mkdtemp(prefix="hms-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["STORAGE_BACKEND"] = "local"
os.environ["LOCAL_STORAGE_DIR"] = f"{_tmp}/uploads"
# Fake AWS credentials so boto3 never touches a real account in tests.
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "us-west-1"

import uuid  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

PDF_BYTES = b"%PDF-1.4\n%fake test pdf\n"


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def register_and_login(client, role="patient"):
    """Create a fresh user and return auth headers for them."""
    email = f"{role}-{uuid.uuid4().hex[:8]}@test.com"
    password = "Password123"
    r = client.post(
        "/auth/register",
        json={"email": email, "full_name": "Test User", "password": password, "role": role},
    )
    assert r.status_code == 201, r.text
    r = client.post("/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def my_patient_id(client, headers):
    r = client.get("/patients/my", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["id"]

# tests/test_documents.py
#
# Run with:  pytest -v
#
# Two kinds of tests:
#   1. API tests with LocalStorage: the upload/permission logic
#   2. S3 tests with moto: the real boto3 code against a fake in-memory S3

import pytest
from moto import mock_aws

from app.core.storage import S3Storage, get_storage, make_s3_client
from main import app
from tests.conftest import PDF_BYTES, my_patient_id, register_and_login

BUCKET = "hms-test-documents"


def upload(client, headers, patient_id, content=PDF_BYTES, content_type="application/pdf", name="blood_test.pdf"):
    return client.post(
        f"/documents/patient/{patient_id}",
        headers=headers,
        files={"file": (name, content, content_type)},
        data={"description": "CBC results"},
    )


# ── 1. API + permissions (local storage) ─────────────────────────
def test_patient_uploads_lists_and_downloads_own_document(client):
    headers = register_and_login(client)
    pid = my_patient_id(client, headers)

    r = upload(client, headers, pid)
    assert r.status_code == 201, r.text
    doc = r.json()
    assert doc["original_filename"] == "blood_test.pdf"
    assert doc["size_bytes"] == len(PDF_BYTES)
    assert "storage_key" not in doc  # internal detail never leaks to clients

    r = client.get(f"/documents/patient/{pid}", headers=headers)
    assert [d["id"] for d in r.json()] == [doc["id"]]

    r = client.get(f"/documents/{doc['id']}/download", headers=headers)
    assert r.json()["url"] == f"/documents/{doc['id']}/content"

    r = client.get(f"/documents/{doc['id']}/content", headers=headers)
    assert r.status_code == 200
    assert r.content == PDF_BYTES


def test_patient_cannot_see_another_patients_documents(client):
    alice = register_and_login(client)
    bob = register_and_login(client)
    alice_pid = my_patient_id(client, alice)
    doc_id = upload(client, alice, alice_pid).json()["id"]

    assert client.get(f"/documents/patient/{alice_pid}", headers=bob).status_code == 403
    assert client.get(f"/documents/{doc_id}/download", headers=bob).status_code == 403
    assert upload(client, bob, alice_pid).status_code == 403


def test_doctor_can_upload_for_a_patient(client):
    patient = register_and_login(client)
    doctor = register_and_login(client, role="doctor")
    pid = my_patient_id(client, patient)

    r = upload(client, doctor, pid)
    assert r.status_code == 201, r.text
    # and the patient can see what the doctor uploaded
    assert len(client.get(f"/documents/patient/{pid}", headers=patient).json()) == 1


def test_rejects_wrong_type_and_fake_pdf(client):
    headers = register_and_login(client)
    pid = my_patient_id(client, headers)

    r = upload(client, headers, pid, content=b"MZ...", content_type="application/x-msdownload", name="virus.exe")
    assert r.status_code == 415

    # Claims to be a PDF, but the bytes are not a PDF → magic-byte check catches it
    r = upload(client, headers, pid, content=b"<script>alert(1)</script>", name="fake.pdf")
    assert r.status_code == 400


def test_requires_login(client):
    assert client.get("/documents/patient/1").status_code == 401


# ── 2. Real S3 code against moto's fake S3 ───────────────────────
@pytest.fixture
def s3_storage():
    # mock_aws intercepts every boto3 call inside this block.
    # Nothing leaves your machine, nothing costs money.
    with mock_aws():
        client = make_s3_client("us-west-1")  # same client setup as production
        client.create_bucket(
            Bucket=BUCKET,
            CreateBucketConfiguration={"LocationConstraint": "us-west-1"},
        )
        yield S3Storage(bucket=BUCKET, region="us-west-1", client=client), client


def test_s3_storage_save_load_encrypt_delete(s3_storage):
    storage, client = s3_storage
    storage.save("patients/1/a.pdf", PDF_BYTES, "application/pdf")

    head = client.head_object(Bucket=BUCKET, Key="patients/1/a.pdf")
    assert head["ServerSideEncryption"] == "AES256"   # encrypted at rest
    assert head["ContentType"] == "application/pdf"
    assert storage.load("patients/1/a.pdf") == PDF_BYTES

    storage.delete("patients/1/a.pdf")
    assert client.list_objects_v2(Bucket=BUCKET).get("KeyCount") == 0


def test_s3_presigned_url_is_signed_and_expires(s3_storage):
    storage, _ = s3_storage
    url = storage.get_download_url("patients/1/a.pdf", "report.pdf")
    assert url.startswith(f"https://{BUCKET}.s3")
    assert "X-Amz-Signature=" in url      # the cryptographic signature
    assert "X-Amz-Expires=300" in url     # valid for 5 minutes only


def test_full_upload_flow_with_s3_backend(client, s3_storage):
    storage, s3 = s3_storage
    # Swap the storage dependency: the router code is unchanged.
    app.dependency_overrides[get_storage] = lambda: storage

    headers = register_and_login(client)
    pid = my_patient_id(client, headers)
    doc = upload(client, headers, pid).json()

    keys = [o["Key"] for o in s3.list_objects_v2(Bucket=BUCKET)["Contents"]]
    assert len(keys) == 1 and keys[0].startswith(f"patients/{pid}/")

    link = client.get(f"/documents/{doc['id']}/download", headers=headers).json()
    assert "X-Amz-Signature=" in link["url"] and link["expires_in"] == 300

    assert client.delete(f"/documents/{doc['id']}", headers=headers).status_code == 204
    assert s3.list_objects_v2(Bucket=BUCKET).get("KeyCount") == 0

# tests/test_users_patients_doctors.py
#
# The three "people" parts of the system, and above all their PERMISSIONS.
# In a hospital, "who can see what" matters more than any other feature,
# so most tests here check that a request is ALLOWED or BLOCKED for each role.

from tests.conftest import make_doctor, make_user


# ── Users ────────────────────────────────────────────────────────
def test_only_admin_can_list_users(client, admin, patient, doctor):
    assert client.get("/users/", headers=admin.headers).status_code == 200
    assert client.get("/users/", headers=patient.headers).status_code == 403
    assert client.get("/users/", headers=doctor.headers).status_code == 403


def test_user_can_view_self_but_not_others(client, patient, other_patient, admin):
    assert client.get(f"/users/{patient.id}", headers=patient.headers).status_code == 200
    assert client.get(f"/users/{other_patient.id}", headers=patient.headers).status_code == 403
    assert client.get(f"/users/{patient.id}", headers=admin.headers).status_code == 200


def test_user_can_update_own_name_only(client, patient, other_patient):
    r = client.patch(f"/users/{patient.id}", headers=patient.headers, json={"full_name": "New Name"})
    assert r.status_code == 200 and r.json()["full_name"] == "New Name"
    r = client.patch(f"/users/{other_patient.id}", headers=patient.headers, json={"full_name": "Hacked"})
    assert r.status_code == 403


def test_only_admin_can_deactivate(client, admin, patient, other_patient):
    assert client.delete(f"/users/{other_patient.id}", headers=patient.headers).status_code == 403
    assert client.delete(f"/users/{other_patient.id}", headers=admin.headers).status_code == 204


# ── Patients ─────────────────────────────────────────────────────
def test_only_admin_can_list_patients(client, admin, patient):
    assert client.get("/patients/", headers=admin.headers).status_code == 200
    assert client.get("/patients/", headers=patient.headers).status_code == 403


def test_patient_sees_and_edits_only_own_profile(client, patient, other_patient):
    assert client.get(f"/patients/{patient.patient_id}", headers=patient.headers).status_code == 200
    assert client.get(f"/patients/{other_patient.patient_id}", headers=patient.headers).status_code == 403

    r = client.patch(f"/patients/{patient.patient_id}", headers=patient.headers,
                     json={"blood_type": "O+", "phone": "555-0100"})
    assert r.status_code == 200
    assert r.json()["blood_type"] == "O+"

    r = client.patch(f"/patients/{other_patient.patient_id}", headers=patient.headers, json={"blood_type": "AB-"})
    assert r.status_code == 403


def test_doctor_can_view_a_patient(client, doctor, patient):
    # Doctors need patient details to treat them.
    assert client.get(f"/patients/{patient.patient_id}", headers=doctor.headers).status_code == 200


def test_missing_patient_is_404(client, admin):
    assert client.get("/patients/999999", headers=admin.headers).status_code == 404


# ── Doctors ──────────────────────────────────────────────────────
def test_any_logged_in_user_can_list_and_filter_doctors(client, patient):
    make_doctor(client, specialization="Neurology")
    make_doctor(client, specialization="Pediatrics")

    r = client.get("/doctors/", headers=patient.headers, params={"specialization": "neuro", "limit": 100})
    assert r.status_code == 200
    specs = {d["specialization"] for d in r.json()}
    assert specs == {"Neurology"}   # "neuro" matched case-insensitively, nothing else


def test_doctors_list_requires_login(client):
    assert client.get("/doctors/").status_code == 401


def test_patient_cannot_create_doctor_profile(client, patient):
    r = client.post("/doctors/", headers=patient.headers,
                    json={"user_id": patient.id, "specialization": "Surgery", "license_number": "LIC-0001"})
    assert r.status_code == 403


def test_doctor_cannot_create_profile_for_someone_else(client):
    me = make_user(client, "doctor")
    other = make_user(client, "doctor")
    r = client.post("/doctors/", headers=me.headers,
                    json={"user_id": other.id, "specialization": "Surgery", "license_number": "LIC-0002"})
    assert r.status_code == 403


def test_duplicate_license_number_is_rejected(client, admin):
    first = make_user(client, "doctor")
    second = make_user(client, "doctor")
    body = {"specialization": "Surgery", "license_number": "LIC-SAME-01"}
    assert client.post("/doctors/", headers=admin.headers, json={**body, "user_id": first.id}).status_code == 201
    assert client.post("/doctors/", headers=admin.headers, json={**body, "user_id": second.id}).status_code == 409


def test_doctor_profile_requires_doctor_role(client, admin, patient):
    r = client.post("/doctors/", headers=admin.headers,
                    json={"user_id": patient.id, "specialization": "Surgery", "license_number": "LIC-0003"})
    assert r.status_code == 400


def test_doctor_updates_only_own_profile(client, doctor):
    other = make_doctor(client)
    r = client.patch(f"/doctors/{doctor.doctor_id}", headers=doctor.headers, json={"consultation_fee": "200.00"})
    assert r.status_code == 200
    assert float(r.json()["consultation_fee"]) == 200.0
    r = client.patch(f"/doctors/{other.doctor_id}", headers=doctor.headers, json={"consultation_fee": "1.00"})
    assert r.status_code == 403


def test_negative_fee_is_rejected(client, doctor):
    r = client.patch(f"/doctors/{doctor.doctor_id}", headers=doctor.headers, json={"consultation_fee": "-5"})
    assert r.status_code == 422

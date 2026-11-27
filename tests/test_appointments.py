# tests/test_appointments.py
#
# Booking rules: who can book, double-booking prevention, and the status
# lifecycle (scheduled → completed / cancelled / no_show).

from datetime import datetime, timedelta

from tests.conftest import book, future, make_doctor


def test_patient_books_appointment_with_names_filled_in(client, patient, doctor):
    r = book(client, patient, patient.patient_id, doctor.doctor_id)
    assert r.status_code == 201, r.text
    appt = r.json()
    assert appt["status"] == "scheduled"
    assert appt["duration_minutes"] == 30           # default
    assert appt["patient_name"] == "Test Patient"
    assert appt["doctor_name"] == "Test Doctor"


def test_patient_cannot_book_for_someone_else(client, patient, other_patient, doctor):
    # The router overwrites patient_id with the caller's own id,
    # so trying to book for another patient books for yourself instead.
    r = book(client, patient, other_patient.patient_id, doctor.doctor_id)
    assert r.status_code == 201
    assert r.json()["patient_id"] == patient.patient_id


def test_cannot_book_in_the_past(client, patient, doctor):
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    assert book(client, patient, patient.patient_id, doctor.doctor_id, when=yesterday).status_code == 422


def test_unknown_doctor_is_404(client, patient):
    assert book(client, patient, patient.patient_id, 999999).status_code == 404


def test_doctor_cannot_be_double_booked(client, patient, other_patient, doctor):
    slot = future(days=2, hour=9)
    assert book(client, patient, patient.patient_id, doctor.doctor_id, when=slot).status_code == 201
    # Same doctor, overlapping time (9:15 is inside the 9:00–9:30 slot)
    overlapping = slot.replace("09:00:00", "09:15:00")
    r = book(client, other_patient, other_patient.patient_id, doctor.doctor_id, when=overlapping)
    assert r.status_code == 409


def test_back_to_back_slots_are_allowed(client, patient, other_patient, doctor):
    slot = future(days=3, hour=9)
    assert book(client, patient, patient.patient_id, doctor.doctor_id, when=slot).status_code == 201
    # 9:30 starts exactly when the 9:00 one ends → no overlap
    r = book(client, other_patient, other_patient.patient_id, doctor.doctor_id,
             when=slot.replace("09:00:00", "09:30:00"))
    assert r.status_code == 201


def test_my_appointments_for_patient_and_doctor(client, patient, doctor):
    appt_id = book(client, patient, patient.patient_id, doctor.doctor_id).json()["id"]
    assert [a["id"] for a in client.get("/appointments/my", headers=patient.headers).json()] == [appt_id]
    assert [a["id"] for a in client.get("/appointments/my", headers=doctor.headers).json()] == [appt_id]


def test_strangers_cannot_view_appointment(client, patient, other_patient, doctor):
    appt_id = book(client, patient, patient.patient_id, doctor.doctor_id).json()["id"]
    other_doctor = make_doctor(client)
    assert client.get(f"/appointments/{appt_id}", headers=patient.headers).status_code == 200
    assert client.get(f"/appointments/{appt_id}", headers=other_patient.headers).status_code == 403
    assert client.get(f"/appointments/{appt_id}", headers=other_doctor.headers).status_code == 403


def test_patient_can_only_cancel(client, patient, doctor):
    appt_id = book(client, patient, patient.patient_id, doctor.doctor_id).json()["id"]
    url = f"/appointments/{appt_id}"

    assert client.patch(url, headers=patient.headers, json={"status": "completed"}).status_code == 403
    assert client.patch(url, headers=patient.headers, json={"notes": "I feel fine"}).status_code == 403

    r = client.patch(url, headers=patient.headers, json={"status": "cancelled"})
    assert r.status_code == 200 and r.json()["status"] == "cancelled"


def test_doctor_completes_with_notes_and_then_it_is_locked(client, patient, doctor):
    appt_id = book(client, patient, patient.patient_id, doctor.doctor_id).json()["id"]
    url = f"/appointments/{appt_id}"

    r = client.patch(url, headers=doctor.headers, json={"status": "completed", "notes": "BP normal"})
    assert r.status_code == 200
    assert r.json()["notes"] == "BP normal"

    # A completed appointment is history: it can't be changed or cancelled.
    assert client.patch(url, headers=doctor.headers, json={"notes": "edit"}).status_code == 400
    assert client.delete(url, headers=patient.headers).status_code == 400


def test_cancel_twice_is_rejected(client, patient, doctor):
    appt_id = book(client, patient, patient.patient_id, doctor.doctor_id).json()["id"]
    assert client.delete(f"/appointments/{appt_id}", headers=patient.headers).status_code == 204
    assert client.delete(f"/appointments/{appt_id}", headers=patient.headers).status_code == 400


def test_cancelled_slot_can_be_rebooked(client, patient, other_patient, doctor):
    slot = future(days=4, hour=14)
    appt_id = book(client, patient, patient.patient_id, doctor.doctor_id, when=slot).json()["id"]
    client.delete(f"/appointments/{appt_id}", headers=patient.headers)
    assert book(client, other_patient, other_patient.patient_id, doctor.doctor_id, when=slot).status_code == 201


def test_duration_limits(client, patient, doctor):
    body = {"patient_id": patient.patient_id, "doctor_id": doctor.doctor_id, "scheduled_at": future()}
    assert client.post("/appointments/", headers=patient.headers, json={**body, "duration_minutes": 5}).status_code == 422
    assert client.post("/appointments/", headers=patient.headers, json={**body, "duration_minutes": 500}).status_code == 422

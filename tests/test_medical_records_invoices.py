# tests/test_medical_records_invoices.py
#
# Clinical data (records, prescriptions, lab results) and billing (invoices).
# Two things are tested hardest here:
#   1. Patients can READ their own data but never WRITE clinical data.
#   2. Money is computed on the SERVER, never trusted from the client.

from decimal import Decimal

import pytest

from tests.conftest import make_doctor


def create_record(client, doctor, patient):
    r = client.post(
        "/medical-records/",
        headers=doctor.headers,
        json={"patient_id": patient.patient_id, "doctor_id": doctor.doctor_id,
              "diagnosis": "Hypertension", "symptoms": "Headache", "treatment": "Rest"},
    )
    assert r.status_code == 201, r.text
    return r.json()


# ── Medical records ──────────────────────────────────────────────
def test_doctor_creates_record_and_patient_reads_it(client, doctor, patient):
    record = create_record(client, doctor, patient)
    r = client.get("/medical-records/my", headers=patient.headers)
    assert [x["id"] for x in r.json()] == [record["id"]]
    assert client.get(f"/medical-records/{record['id']}", headers=patient.headers).status_code == 200


def test_doctor_id_comes_from_token_not_request(client, doctor, patient):
    # A doctor sends someone else's doctor_id → the server uses their real one.
    other = make_doctor(client)
    r = client.post("/medical-records/", headers=doctor.headers,
                    json={"patient_id": patient.patient_id, "doctor_id": other.doctor_id, "diagnosis": "Flu"})
    assert r.status_code == 201
    assert r.json()["doctor_id"] == doctor.doctor_id


def test_patient_cannot_create_or_edit_records(client, doctor, patient):
    record = create_record(client, doctor, patient)
    r = client.post("/medical-records/", headers=patient.headers,
                    json={"patient_id": patient.patient_id, "doctor_id": doctor.doctor_id, "diagnosis": "Self-diagnosed"})
    assert r.status_code == 403
    r = client.patch(f"/medical-records/{record['id']}", headers=patient.headers, json={"diagnosis": "Nothing"})
    assert r.status_code == 403


def test_patient_cannot_read_another_patients_records(client, doctor, patient, other_patient):
    record = create_record(client, doctor, patient)
    assert client.get(f"/medical-records/{record['id']}", headers=other_patient.headers).status_code == 403
    assert client.get(f"/medical-records/patient/{patient.patient_id}", headers=other_patient.headers).status_code == 403


def test_only_authoring_doctor_can_edit_record(client, doctor, patient):
    record = create_record(client, doctor, patient)
    other = make_doctor(client)
    r = client.patch(f"/medical-records/{record['id']}", headers=other.headers, json={"diagnosis": "Changed"})
    assert r.status_code in (403, 404)
    r = client.patch(f"/medical-records/{record['id']}", headers=doctor.headers, json={"diagnosis": "Stage 1 HTN"})
    assert r.status_code == 200 and r.json()["diagnosis"] == "Stage 1 HTN"


def test_prescription_and_lab_result_flow(client, doctor, patient):
    record = create_record(client, doctor, patient)
    rid = record["id"]

    r = client.post(f"/medical-records/{rid}/prescriptions", headers=doctor.headers,
                    json={"medical_record_id": rid, "doctor_id": doctor.doctor_id,
                          "medication_name": "Lisinopril", "dosage": "10mg", "frequency": "Once daily"})
    assert r.status_code == 201, r.text
    rx_id = r.json()["id"]
    r = client.patch(f"/medical-records/prescriptions/{rx_id}", headers=doctor.headers, json={"dosage": "20mg"})
    assert r.status_code == 200 and r.json()["dosage"] == "20mg"

    r = client.post(f"/medical-records/{rid}/lab-results", headers=doctor.headers,
                    json={"medical_record_id": rid, "test_name": "Lipid panel"})
    assert r.status_code == 201, r.text
    lab = r.json()
    assert lab["status"] == "pending"
    r = client.patch(f"/medical-records/lab-results/{lab['id']}", headers=doctor.headers,
                     json={"status": "completed", "result_value": "LDL 95 mg/dL"})
    assert r.status_code == 200 and r.json()["result_value"] == "LDL 95 mg/dL"

    # The patient sees both inside their record
    full = client.get(f"/medical-records/{rid}", headers=patient.headers).json()
    assert len(full["prescriptions"]) == 1 and len(full["lab_results"]) == 1


def test_patient_cannot_prescribe_or_order_labs(client, doctor, patient):
    rid = create_record(client, doctor, patient)["id"]
    r = client.post(f"/medical-records/{rid}/prescriptions", headers=patient.headers,
                    json={"medical_record_id": rid, "doctor_id": doctor.doctor_id,
                          "medication_name": "Oxycodone", "dosage": "80mg", "frequency": "Hourly"})
    assert r.status_code == 403
    r = client.post(f"/medical-records/{rid}/lab-results", headers=patient.headers,
                    json={"medical_record_id": rid, "test_name": "X"})
    assert r.status_code == 403


# ── Invoices ─────────────────────────────────────────────────────
def create_invoice(client, creator, patient, items=None):
    return client.post(
        "/invoices/",
        headers=creator.headers,
        json={"patient_id": patient.patient_id,
              "items": items if items is not None else [{"description": "Consultation", "quantity": 1, "unit_price": "100.00"},
                                 {"description": "Blood test", "quantity": 2, "unit_price": "25.00"}]},
    )


def test_invoice_totals_are_computed_by_server(client, doctor, patient):
    r = create_invoice(client, doctor, patient)
    assert r.status_code == 201, r.text
    inv = r.json()
    # 100 + 2×25 = 150 subtotal, 8% tax = 12.00, total = 162.00
    assert Decimal(inv["subtotal"]) == Decimal("150.00")
    assert Decimal(inv["tax_amount"]) == Decimal("12.00")
    assert Decimal(inv["total_amount"]) == Decimal("162.00")
    assert inv["status"] == "pending"


def test_client_sent_item_total_is_ignored(client, doctor, patient):
    items = [{"description": "MRI", "quantity": 1, "unit_price": "500.00", "total_price": "0.01"}]
    inv = create_invoice(client, doctor, patient, items=items).json()
    assert Decimal(inv["subtotal"]) == Decimal("500.00")


def test_invoice_needs_at_least_one_item(client, doctor, patient):
    assert create_invoice(client, doctor, patient, items=[]).status_code == 422


def test_patient_cannot_create_or_list_all_invoices(client, patient):
    assert create_invoice(client, patient, patient).status_code == 403
    assert client.get("/invoices/", headers=patient.headers).status_code == 403


def test_patient_sees_only_own_invoices(client, doctor, patient, other_patient):
    inv_id = create_invoice(client, doctor, patient).json()["id"]
    assert [i["id"] for i in client.get("/invoices/my", headers=patient.headers).json()] == [inv_id]
    assert client.get("/invoices/my", headers=other_patient.headers).json() == []
    assert client.get(f"/invoices/{inv_id}", headers=other_patient.headers).status_code == 403
    assert client.get(f"/invoices/patient/{patient.patient_id}", headers=other_patient.headers).status_code == 403


def test_patient_can_pay_own_invoice_but_not_waive_it(client, doctor, patient):
    inv_id = create_invoice(client, doctor, patient).json()["id"]
    r = client.patch(f"/invoices/{inv_id}", headers=patient.headers, json={"status": "waived"})
    assert r.status_code == 403
    r = client.patch(f"/invoices/{inv_id}", headers=patient.headers, json={"status": "paid"})
    assert r.status_code == 200 and r.json()["status"] == "paid"


def test_filter_invoices_by_status(client, doctor, patient):
    create_invoice(client, doctor, patient)
    r = client.get("/invoices/", headers=doctor.headers, params={"payment_status": "pending", "limit": 100})
    assert r.status_code == 200 and all(i["status"] == "pending" for i in r.json())
    assert client.get("/invoices/", headers=doctor.headers, params={"payment_status": "bogus"}).status_code == 422


@pytest.mark.xfail(
    strict=True,
    reason="KNOWN SECURITY BUG: a patient can send {'discount': ...} on their own invoice "
           "and lower the total. The router only checks 'status'. Fix it, then delete this marker.",
)
def test_patient_cannot_discount_own_invoice(client, doctor, patient):
    inv_id = create_invoice(client, doctor, patient).json()["id"]
    r = client.patch(f"/invoices/{inv_id}", headers=patient.headers, json={"discount": "150.00"})
    assert r.status_code == 403

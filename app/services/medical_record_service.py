# app/services/medical_record_service.py

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.models.medical_record import MedicalRecord
from app.models.prescription import Prescription
from app.models.lab_result import LabResult, LabStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.schemas.medical_record import (
    MedicalRecordCreate, MedicalRecordUpdate,
    PrescriptionCreate, PrescriptionUpdate,
    LabResultCreate, LabResultUpdate,
)
from datetime import datetime, timezone


def _load_record_or_404(db: Session, record_id: int) -> MedicalRecord:
    record = (
        db.query(MedicalRecord)
        .options(
            joinedload(MedicalRecord.patient).joinedload(Patient.user),
            joinedload(MedicalRecord.doctor).joinedload(Doctor.user),
            joinedload(MedicalRecord.prescriptions),
            joinedload(MedicalRecord.lab_results),
        )
        .filter(MedicalRecord.id == record_id)
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Medical record {record_id} not found"
        )
    return record


def create_medical_record(
    db: Session,
    data: MedicalRecordCreate,
    requesting_doctor_id: int,
) -> MedicalRecord:
    patient = db.query(Patient).filter(Patient.id == data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {data.patient_id} not found")

    doctor = db.query(Doctor).filter(Doctor.id == data.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail=f"Doctor {data.doctor_id} not found")

    if data.appointment_id:
        appt = db.query(Appointment).filter(Appointment.id == data.appointment_id).first()
        if not appt:
            raise HTTPException(status_code=404, detail=f"Appointment {data.appointment_id} not found")
        if appt.doctor_id != requesting_doctor_id:
            raise HTTPException(status_code=403, detail="You can only create records for your own appointments")
        if appt.patient_id != data.patient_id:
            raise HTTPException(status_code=400, detail="Patient does not match the appointment's patient")

    if data.appointment_id:
        existing = db.query(MedicalRecord).filter(
            MedicalRecord.appointment_id == data.appointment_id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"A medical record already exists for appointment {data.appointment_id}")

    record = MedicalRecord(**data.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return _load_record_or_404(db, record.id)


def get_medical_record(db: Session, record_id: int) -> MedicalRecord:
    return _load_record_or_404(db, record_id)


def get_records_for_patient(db: Session, patient_id: int) -> list[MedicalRecord]:
    return (
        db.query(MedicalRecord)
        .options(
            joinedload(MedicalRecord.doctor).joinedload(Doctor.user),
            joinedload(MedicalRecord.prescriptions),
            joinedload(MedicalRecord.lab_results),
        )
        .filter(MedicalRecord.patient_id == patient_id)
        .order_by(MedicalRecord.created_at.desc())
        .all()
    )


def get_records_by_doctor(db: Session, doctor_id: int) -> list[MedicalRecord]:
    return (
        db.query(MedicalRecord)
        .options(
            joinedload(MedicalRecord.patient).joinedload(Patient.user),
            joinedload(MedicalRecord.prescriptions),
            joinedload(MedicalRecord.lab_results),
        )
        .filter(MedicalRecord.doctor_id == doctor_id)
        .order_by(MedicalRecord.created_at.desc())
        .all()
    )


def update_medical_record(
    db: Session,
    record_id: int,
    data: MedicalRecordUpdate,
    requesting_doctor_id: int,
) -> MedicalRecord:
    record = _load_record_or_404(db, record_id)
    if record.doctor_id != requesting_doctor_id:
        raise HTTPException(status_code=403, detail="You can only update records you created")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return _load_record_or_404(db, record_id)


def add_prescription(
    db: Session,
    data: PrescriptionCreate,
    requesting_doctor_id: int,
) -> Prescription:
    record = _load_record_or_404(db, data.medical_record_id)
    if record.doctor_id != requesting_doctor_id:
        raise HTTPException(status_code=403, detail="You can only prescribe on records you created")
    prescription = Prescription(**data.model_dump())
    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    return prescription


def update_prescription(
    db: Session,
    prescription_id: int,
    data: PrescriptionUpdate,
    requesting_doctor_id: int,
) -> Prescription:
    rx = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not rx:
        raise HTTPException(status_code=404, detail=f"Prescription {prescription_id} not found")
    record = _load_record_or_404(db, rx.medical_record_id)
    if record.doctor_id != requesting_doctor_id:
        raise HTTPException(status_code=403, detail="Access denied")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rx, field, value)
    db.commit()
    db.refresh(rx)
    return rx


def order_lab_test(
    db: Session,
    data: LabResultCreate,
    requesting_doctor_id: int,
) -> LabResult:
    record = _load_record_or_404(db, data.medical_record_id)
    if record.doctor_id != requesting_doctor_id:
        raise HTTPException(status_code=403, detail="You can only order tests on records you created")
    lab = LabResult(**data.model_dump())
    db.add(lab)
    db.commit()
    db.refresh(lab)
    return lab


def update_lab_result(
    db: Session,
    lab_id: int,
    data: LabResultUpdate,
    requesting_doctor_id: int,
) -> LabResult:
    lab = db.query(LabResult).filter(LabResult.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail=f"Lab result {lab_id} not found")
    record = _load_record_or_404(db, lab.medical_record_id)
    if record.doctor_id != requesting_doctor_id:
        raise HTTPException(status_code=403, detail="Access denied")
    updates = data.model_dump(exclude_unset=True)
    if updates.get("status") == LabStatus.completed and not lab.completed_at:
        updates["completed_at"] = datetime.now(timezone.utc)
    for field, value in updates.items():
        setattr(lab, field, value)
    db.commit()
    db.refresh(lab)
    return lab
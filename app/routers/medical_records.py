# app/routers/medical_records.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, cast
from app.core.db import get_db
from app.core.dependencies import get_current_active_user
from app.schemas.medical_record import (
    MedicalRecordCreate, MedicalRecordUpdate, MedicalRecordResponse,
    PrescriptionCreate, PrescriptionUpdate, PrescriptionResponse,
    LabResultCreate, LabResultUpdate, LabResultResponse,
)
from app.services import medical_record_service, patient_service, doctor_service
from app.models.user import User, UserRole
from app.models.medical_record import MedicalRecord

router = APIRouter(prefix="/medical-records", tags=["Medical Records"])


def _get_user_id(user: User) -> int:
    """Return ORM user id as plain int for typed service calls."""
    return cast(int, user.id)


def _get_doctor_id_or_403(db: Session, current_user: User) -> int:
    """
    Get the Doctor.id for the current user, or raise 403.
    Centralizes the 'is this user a doctor?' check.
    """
    profile = doctor_service.get_doctor_by_user_id(db, _get_user_id(current_user))
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You need a doctor profile to perform this action"
        )
    return cast(int, profile.id)


def _has_role(user: User, role: UserRole) -> bool:
    """Type-safe role comparison for ORM user instances."""
    return cast(UserRole, user.role) == role


# ── Medical Records ───────────────────────────────────────────────

@router.post("/", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
def create_medical_record(
    data: MedicalRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a medical record. Doctors only.
    The doctor_id in the request is validated against the calling user.
    """
    if _has_role(current_user, UserRole.patient):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patients cannot create medical records"
        )

    doctor_id = (
        _get_doctor_id_or_403(db, current_user)
        if _has_role(current_user, UserRole.doctor)
        else data.doctor_id   # admin can specify any doctor
    )

    return medical_record_service.create_medical_record(db, data, doctor_id)


@router.get("/patient/{patient_id}", response_model=List[MedicalRecordResponse])
def get_patient_records(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all medical records for a patient.
    - Patient: own records only
    - Doctor: any patient's records (they may need patient history)
    - Admin: all
    """
    if _has_role(current_user, UserRole.patient):
        own = patient_service.get_patient_by_user_id(db, _get_user_id(current_user))
        if own is None or cast(int, own.id) != patient_id:
            raise HTTPException(status_code=403, detail="Access denied")

    return medical_record_service.get_records_for_patient(db, patient_id)


@router.get("/my", response_model=List[MedicalRecordResponse])
def get_my_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[MedicalRecord]:
    """
    Convenience endpoint:
    - Patient: returns their own medical records
    - Doctor: returns records THEY wrote
    """
    if _has_role(current_user, UserRole.patient):
        profile = patient_service.get_patient_by_user_id(db, _get_user_id(current_user))
        if not profile:
            return cast(List[MedicalRecord], [])
        return medical_record_service.get_records_for_patient(db, cast(int, profile.id))

    elif _has_role(current_user, UserRole.doctor):
        profile = doctor_service.get_doctor_by_user_id(db, _get_user_id(current_user))
        if not profile:
            return cast(List[MedicalRecord], [])
        return medical_record_service.get_records_by_doctor(db, cast(int, profile.id))

    # Admin — not implemented here; use /patient/{id} or /doctor/{id}
    raise HTTPException(status_code=400, detail="Admins: use /patient/{id} or /doctor/{id}")


@router.get("/{record_id}", response_model=MedicalRecordResponse)
def get_medical_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    record = medical_record_service.get_medical_record(db, record_id)

    # Patients can only see their own records
    if _has_role(current_user, UserRole.patient):
        own = patient_service.get_patient_by_user_id(db, _get_user_id(current_user))
        if own is None or cast(int, record.patient_id) != cast(int, own.id):
            raise HTTPException(status_code=403, detail="Access denied")

    return record


@router.patch("/{record_id}", response_model=MedicalRecordResponse)
def update_medical_record(
    record_id: int,
    data: MedicalRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a medical record. Only the authoring doctor (or admin) can edit."""
    if _has_role(current_user, UserRole.patient):
        raise HTTPException(status_code=403, detail="Patients cannot edit medical records")

    doctor_id = (
        _get_doctor_id_or_403(db, current_user)
        if _has_role(current_user, UserRole.doctor)
        else cast(int, medical_record_service.get_medical_record(db, record_id).doctor_id)
    )

    return medical_record_service.update_medical_record(db, record_id, data, doctor_id)


# ── Prescriptions ─────────────────────────────────────────────────

@router.post("/{record_id}/prescriptions", response_model=PrescriptionResponse, status_code=201)
def add_prescription(
    record_id: int,
    data: PrescriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add a prescription to a medical record. Doctors only."""
    if _has_role(current_user, UserRole.patient):
        raise HTTPException(status_code=403, detail="Patients cannot add prescriptions")

    doctor_id = _get_doctor_id_or_403(db, current_user)

    # Lock medical_record_id to the URL param — prevents client from
    # adding a prescription to a different record than the URL specifies
    data.medical_record_id = record_id

    return medical_record_service.add_prescription(db, data, doctor_id)


@router.patch("/prescriptions/{prescription_id}", response_model=PrescriptionResponse)
def update_prescription(
    prescription_id: int,
    data: PrescriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if _has_role(current_user, UserRole.patient):
        raise HTTPException(status_code=403, detail="Access denied")

    doctor_id = _get_doctor_id_or_403(db, current_user)
    return medical_record_service.update_prescription(db, prescription_id, data, doctor_id)


# ── Lab Results ───────────────────────────────────────────────────

@router.post("/{record_id}/lab-results", response_model=LabResultResponse, status_code=201)
def order_lab_test(
    record_id: int,
    data: LabResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Order a lab test (creates a pending LabResult). Doctors only."""
    if _has_role(current_user, UserRole.patient):
        raise HTTPException(status_code=403, detail="Access denied")

    doctor_id = _get_doctor_id_or_403(db, current_user)
    data.medical_record_id = record_id

    return medical_record_service.order_lab_test(db, data, doctor_id)


@router.patch("/lab-results/{lab_id}", response_model=LabResultResponse)
def update_lab_result(
    lab_id: int,
    data: LabResultUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Fill in lab results (e.g. mark as completed with result values). Doctors only."""
    if _has_role(current_user, UserRole.patient):
        raise HTTPException(status_code=403, detail="Access denied")

    doctor_id = _get_doctor_id_or_403(db, current_user)
    return medical_record_service.update_lab_result(db, lab_id, data, doctor_id)
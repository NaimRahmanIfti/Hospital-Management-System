# app/routers/patients.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.core.db import get_db
from app.core.dependencies import get_current_active_user, require_admin
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from app.services import patient_service
from app.models.user import User, UserRole

router = APIRouter(prefix="/patients", tags=["Patients"])


def _require_own_or_admin(current_user: User, patient_user_id: int):
    if current_user.role == UserRole.admin:
        return
    if current_user.id != patient_user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own patient profile"
        )


@router.get("/", response_model=List[PatientResponse])
def list_patients(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return patient_service.get_all_patients(db, skip, limit)


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(
    data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role != UserRole.admin:
        data.user_id = current_user.id
    return patient_service.create_patient_profile(db, data)


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    patient = patient_service.get_patient_by_id(db, patient_id)
    if current_user.role == UserRole.patient:
        _require_own_or_admin(current_user, patient.user_id)
    return patient


@router.patch("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: int,
    data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    patient = patient_service.get_patient_by_id(db, patient_id)
    _require_own_or_admin(current_user, patient.user_id)
    return patient_service.update_patient_profile(db, patient_id, data)
# app/routers/patients.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, cast
from app.core.db import get_db
from app.core.dependencies import get_current_active_user, require_admin
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from app.services import patient_service
from app.models.user import User

router = APIRouter(prefix="/patients", tags=["Patients"])


def _require_own_or_admin(current_user: User, patient_user_id: int):
    """
    Helper: allow access if user owns this patient profile OR is admin.
    We define this as a local function (not a Depends) because it needs
    a runtime value (patient_user_id) that isn't known at import time.
    """
    role_value = str(getattr(current_user.role, "value", current_user.role))
    if role_value == "admin":
        return   # admin can always proceed

    current_user_id = cast(int, current_user.id)
    if current_user_id != patient_user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own patient profile"
        )


# ── GET /patients ─────────────────────────────────────────────────
@router.get("/", response_model=List[PatientResponse])
def list_patients(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),    # admin only
):
    return patient_service.get_all_patients(db, skip, limit)


# ── POST /patients ────────────────────────────────────────────────
@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(
    data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a patient profile.
    Patients create their own; admins can create for any user.
    """
    role_value = str(getattr(current_user.role, "value", current_user.role))
    if role_value != "admin":
        # Force user_id to be the calling user's ID
        # Prevents a patient from creating a profile for someone else
        data.user_id = cast(int, current_user.id)

    return patient_service.create_patient_profile(db, data)


# ── GET /patients/{patient_id} ────────────────────────────────────
@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    patient = patient_service.get_patient_by_id(db, patient_id)

    # Doctors can view any patient profile (they need it for appointments)
    # Admins can view any profile
    # Patients can only view their own
    role_value = str(getattr(current_user.role, "value", current_user.role))
    if role_value == "patient":
        _require_own_or_admin(current_user, cast(int, patient.user_id))

    return patient


# ── PATCH /patients/{patient_id} ──────────────────────────────────
@router.patch("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: int,
    data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    patient = patient_service.get_patient_by_id(db, patient_id)
    _require_own_or_admin(current_user, cast(int, patient.user_id))
    return patient_service.update_patient_profile(db, patient_id, data)
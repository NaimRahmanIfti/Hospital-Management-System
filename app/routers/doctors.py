# app/routers/doctors.py

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.db import get_db
from app.core.dependencies import get_current_active_user, require_admin
from app.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorResponse
from app.services import doctor_service
from app.models.user import User

router = APIRouter(prefix="/doctors", tags=["Doctors"])


# ── GET /doctors ──────────────────────────────────────────────────
# Any authenticated user can list doctors (patients need to pick one)
@router.get("/", response_model=List[DoctorResponse])
def list_doctors(
    skip: int = 0,
    limit: int = 20,
    # Query() lets us add metadata + validation to query params
    # ?specialization=cardio → filters by specialization (case-insensitive)
    specialization: Optional[str] = Query(None, description="Filter by specialization"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return doctor_service.get_all_doctors(db, skip, limit, specialization)


# ── POST /doctors ─────────────────────────────────────────────────
@router.post("/", response_model=DoctorResponse, status_code=status.HTTP_201_CREATED)
def create_doctor(
    data: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Admin can create a doctor profile for any user.
    A doctor-role user can create their own profile (user_id must match).
    """
    from fastapi import HTTPException
    from app.models.user import UserRole
    role_val = str(getattr(current_user.role, "value", current_user.role)).lower()
    if role_val == "patient":
        raise HTTPException(status_code=403, detail="Patients cannot create doctor profiles")
    if role_val == "doctor" and int(current_user.id) != int(data.user_id):
        raise HTTPException(status_code=403, detail="Doctors can only create their own profile")
    return doctor_service.create_doctor_profile(db, data)


# ── GET /doctors/{doctor_id} ──────────────────────────────────────
@router.get("/{doctor_id}", response_model=DoctorResponse)
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    return doctor_service.get_doctor_by_id(db, doctor_id)


# ── PATCH /doctors/{doctor_id} ────────────────────────────────────
@router.patch("/{doctor_id}", response_model=DoctorResponse)
def update_doctor(
    doctor_id: int,
    data: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Doctors can update their own profile.
    Admins can update any profile.
    """
    doctor = doctor_service.get_doctor_by_id(db, doctor_id)

    # Is the calling user this doctor?
    role_obj = getattr(current_user, "role", None)
    role_value = getattr(role_obj, "value", role_obj)
    is_admin = str(role_value or "").lower() == "admin"

    current_user_id = getattr(current_user, "id", None)
    doctor_user_id = getattr(doctor, "user_id", None)
    is_owner = (
        current_user_id is not None
        and doctor_user_id is not None
        and str(current_user_id) == str(doctor_user_id)
    )

    if not is_admin and not is_owner:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own doctor profile"
        )

    return doctor_service.update_doctor_profile(db, doctor_id, data)
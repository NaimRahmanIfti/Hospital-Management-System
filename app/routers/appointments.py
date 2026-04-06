# app/routers/appointments.py

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from app.core.db import get_db
from app.core.dependencies import get_current_active_user
from app.schemas.appointment import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse
)
from app.services import appointment_service, patient_service, doctor_service
from app.models.user import User
from app.models.appointment import Appointment, AppointmentStatus

router = APIRouter(prefix="/appointments", tags=["Appointments"])


def _has_role(user_role: object, expected: str) -> bool:
    role_name = getattr(user_role, "value", user_role)
    return str(role_name).lower() == expected.lower()


def _as_int(value: Any) -> int:
    return int(value)


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value)).lower()


def _build_appointment_response(appt: Any) -> dict[str, Any]:
    """
    SQLAlchemy objects don't automatically resolve nested names.
    We manually build the response dict to include patient/doctor names.
    This avoids extra DB queries and keeps the response clean.
    """
    return {
        "id":               appt.id,
        "patient_id":       appt.patient_id,
        "doctor_id":        appt.doctor_id,
        "room_id":          getattr(appt, "room_id", None),
        "scheduled_at":     appt.scheduled_at,
        "duration_minutes": appt.duration_minutes,
        "status":           appt.status,
        "reason":           appt.reason,
        "notes":            appt.notes,
        # Navigate the relationship chain to get names
        # appt.patient.user.full_name — two joins, one already loaded
        "patient_name": appt.patient.user.full_name if appt.patient and appt.patient.user else None,
        "doctor_name":  appt.doctor.user.full_name  if appt.doctor  and appt.doctor.user  else None,
    }


# ── POST /appointments ────────────────────────────────────────────
@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def book_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Book an appointment.
    - Patients can only book for themselves.
    - Doctors and admins can book for any patient.
    - Checks doctor availability automatically.
    """
    payload = data

    # Patients can only book for their own profile
    if _has_role(current_user.role, "patient"):
        own_profile = patient_service.get_patient_by_user_id(db, _as_int(current_user.id))
        if own_profile is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You don't have a patient profile yet. Create one first."
            )
        # Force patient_id to be their own
        payload = data.model_copy(update={"patient_id": _as_int(own_profile.id)})

    appt = appointment_service.book_appointment(db, payload)
    # Reload with relationships for the response
    appt = appointment_service.get_appointment_by_id(db, _as_int(appt.id))
    return _build_appointment_response(appt)


# ── GET /appointments/my ──────────────────────────────────────────
# IMPORTANT: /my must come BEFORE /{appointment_id}
# FastAPI matches routes top-to-bottom.
# If /{appointment_id} came first, "my" would be treated as an integer → 422 error
@router.get("/my", response_model=List[AppointmentResponse])
def get_my_appointments(
    status_filter: Optional[AppointmentStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[dict[str, Any]]:
    """
    Get appointments for the currently logged-in user.
    Works for both patients and doctors — returns the right set.
    """
    appts: List[Any]

    if _has_role(current_user.role, "patient"):
        profile = patient_service.get_patient_by_user_id(db, _as_int(current_user.id))
        if profile is None:
            return []
        appts = appointment_service.get_appointments_for_patient(
            db, _as_int(profile.id), status_filter
        )

    elif _has_role(current_user.role, "doctor"):
        profile = doctor_service.get_doctor_by_user_id(db, _as_int(current_user.id))
        if profile is None:
            return []
        appts = appointment_service.get_appointments_for_doctor(
            db, _as_int(profile.id), status_filter=status_filter
        )

    else:
        # Admin — show all
        appts = db.query(Appointment).order_by(text("scheduled_at DESC")).all()

    return [_build_appointment_response(a) for a in appts]


# ── GET /appointments/{appointment_id} ───────────────────────────
@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    appt = appointment_service.get_appointment_by_id(db, appointment_id)

    # Authorization: patient can only see their own, doctor can only see theirs
    if _has_role(current_user.role, "patient"):
        profile = patient_service.get_patient_by_user_id(db, _as_int(current_user.id))
        if profile is None or _as_int(appt.patient_id) != _as_int(profile.id):
            raise HTTPException(status_code=403, detail="Access denied")

    elif _has_role(current_user.role, "doctor"):
        profile = doctor_service.get_doctor_by_user_id(db, _as_int(current_user.id))
        if profile is None or _as_int(appt.doctor_id) != _as_int(profile.id):
            raise HTTPException(status_code=403, detail="Access denied")

    return _build_appointment_response(appt)


# ── PATCH /appointments/{appointment_id} ─────────────────────────
@router.patch("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: int,
    data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update an appointment.
    - Patients can only cancel (status → cancelled).
    - Doctors can complete, add notes, change room.
    - Admins can do anything.
    """
    appt = appointment_service.get_appointment_by_id(db, appointment_id)

    # Patients: can only touch their own, and only to cancel
    if _has_role(current_user.role, "patient"):
        profile = patient_service.get_patient_by_user_id(db, _as_int(current_user.id))
        if profile is None or _as_int(appt.patient_id) != _as_int(profile.id):
            raise HTTPException(status_code=403, detail="Access denied")

        # Patients can only cancel — nothing else
        allowed_updates = {"status"}
        incoming = set(data.model_dump(exclude_unset=True).keys())
        if incoming - allowed_updates:
            raise HTTPException(
                status_code=403,
                detail="Patients can only cancel appointments (set status=cancelled)"
            )
        if data.status is not None and _enum_value(data.status) != "cancelled":
            raise HTTPException(
                status_code=403,
                detail="Patients can only set status to 'cancelled'"
            )

    # Doctors: can only update their own appointments
    elif _has_role(current_user.role, "doctor"):
        profile = doctor_service.get_doctor_by_user_id(db, _as_int(current_user.id))
        if profile is None or _as_int(appt.doctor_id) != _as_int(profile.id):
            raise HTTPException(status_code=403, detail="Access denied")

    updated = appointment_service.update_appointment(
        db, appointment_id, data, _as_int(current_user.id)
    )
    updated = appointment_service.get_appointment_by_id(db, _as_int(updated.id))
    return _build_appointment_response(updated)


# ── DELETE /appointments/{appointment_id} (cancel) ───────────────
@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Cancel an appointment. Patients cancel their own; admins cancel any."""
    appt = appointment_service.get_appointment_by_id(db, appointment_id)

    if _has_role(current_user.role, "patient"):
        profile = patient_service.get_patient_by_user_id(db, _as_int(current_user.id))
        if profile is None or _as_int(appt.patient_id) != _as_int(profile.id):
            raise HTTPException(status_code=403, detail="Access denied")

    appointment_service.cancel_appointment(db, appointment_id)
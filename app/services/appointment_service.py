# app/services/appointment_service.py

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from typing import Any, cast
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate


# ── Availability check — the heart of booking ─────────────────────
def _check_doctor_availability(
    db: Session,
    doctor_id: int,
    start_time: datetime,
    duration_minutes: int,
    exclude_appointment_id: int | None = None,
) -> None:
    """
    Raise 409 if the doctor already has a conflicting appointment.

    Overlap rule: two ranges [A_start, A_end) and [B_start, B_end) overlap if:
        A_start < B_end  AND  A_end > B_start

    We fetch candidates from the DB (broad filter) then do the precise
    overlap check in Python — works on both SQLite (dev) and PostgreSQL (prod).
    """
    new_end = start_time + timedelta(minutes=duration_minutes)

    # Broad SQL filter: only appointments that start before our slot ends
    scheduled_at_col: Any = getattr(Appointment, "scheduled_at")
    candidates = (
        db.query(Appointment)
        .filter_by(doctor_id=doctor_id, status=AppointmentStatus.SCHEDULED)
        .filter(scheduled_at_col < new_end)   # broad cut: started before we end
        .all()
    )

    conflict: Appointment | None = None
    for existing in candidates:
        existing_id = cast(int, getattr(existing, "id"))
        if exclude_appointment_id is not None and existing_id == exclude_appointment_id:
            continue

        existing_start_value: Any = getattr(existing, "scheduled_at")
        existing_start = cast(datetime, existing_start_value)
        existing_duration_value: Any = getattr(existing, "duration_minutes")
        existing_duration = cast(int, existing_duration_value)
        existing_end: datetime = existing_start + timedelta(minutes=existing_duration)

        if existing_start < new_end and existing_end > start_time:
            conflict = existing
            break

    if conflict:
        conflict_start_value: Any = getattr(conflict, "scheduled_at")
        conflict_start = cast(datetime, conflict_start_value)
        conflict_duration_value: Any = getattr(conflict, "duration_minutes")
        conflict_duration = cast(int, conflict_duration_value)
        conflict_end: datetime = conflict_start + timedelta(minutes=conflict_duration)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Doctor is not available at {start_time.strftime('%Y-%m-%d %H:%M')}. "
                f"Conflict: {conflict_start.strftime('%H:%M')}–{conflict_end.strftime('%H:%M')}"
            )
        )


def get_appointment_by_id(db: Session, appointment_id: int) -> Appointment:
    appt = (
        db.query(Appointment)
        .options(
            joinedload(Appointment.patient).joinedload(Patient.user),
            joinedload(Appointment.doctor).joinedload(Doctor.user),
        )
        .filter(Appointment.id == appointment_id)
        .first()
    )
    if not appt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment {appointment_id} not found"
        )
    return appt


def get_appointments_for_patient(
    db: Session,
    patient_id: int,
    status_filter: AppointmentStatus | None = None,
) -> list[Appointment]:
    """Get all appointments for a patient, optionally filtered by status."""
    query = (
        db.query(Appointment)
        .options(joinedload(Appointment.doctor).joinedload(Doctor.user))
        .filter(Appointment.patient_id == patient_id)
    )
    if status_filter:
        query = query.filter(Appointment.status == status_filter)

    # Most recent first
    scheduled_at_col: Any = getattr(Appointment, "scheduled_at")
    return query.order_by(scheduled_at_col.desc()).all()


def get_appointments_for_doctor(
    db: Session,
    doctor_id: int,
    date: datetime | None = None,       # filter to a specific day
    status_filter: AppointmentStatus | None = None,
) -> list[Appointment]:
    """Get all appointments for a doctor, optionally filtered by date and status."""
    query = (
        db.query(Appointment)
        .options(joinedload(Appointment.patient).joinedload(Patient.user))
        .filter(Appointment.doctor_id == doctor_id)
    )

    scheduled_at_col: Any = getattr(Appointment, "scheduled_at")

    if date:
        # Filter to just the given calendar day
        # Between start of day (00:00:00) and end of day (23:59:59)
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end   = date.replace(hour=23, minute=59, second=59)
        query = query.filter(
            scheduled_at_col.between(day_start, day_end)
        )

    if status_filter:
        query = query.filter(Appointment.status == status_filter)

    return query.order_by(scheduled_at_col.asc()).all()


def book_appointment(db: Session, data: AppointmentCreate) -> Appointment:
    """
    Book an appointment.

    Steps:
    1. Verify patient exists
    2. Verify doctor exists
    3. CHECK AVAILABILITY (the important one)
    4. Create the appointment
    """
    # Step 1: patient must exist
    patient = db.query(Patient).filter(Patient.id == data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {data.patient_id} not found")

    # Step 2: doctor must exist
    doctor = db.query(Doctor).filter(Doctor.id == data.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail=f"Doctor {data.doctor_id} not found")

    # Step 3: check no time conflict for this doctor
    _check_doctor_availability(
        db,
        doctor_id=data.doctor_id,
        start_time=data.scheduled_at,
        duration_minutes=data.duration_minutes,
    )

    # Step 4: create it
    appointment = Appointment(**data.model_dump())
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def update_appointment(
    db: Session,
    appointment_id: int,
    data: AppointmentUpdate,
    requesting_user_id: int,     # who is making this change?
) -> Appointment:
    """
    Update an appointment (reschedule, cancel, add notes).

    Authorization rules:
    - Patient can cancel their own appointment
    - Doctor can complete, add notes, change room
    - Admin can do anything
    We enforce this at the router level — here we just do the work.
    """
    appt = get_appointment_by_id(db, appointment_id)

    # Can't modify a completed or cancelled appointment
    appt_status = cast(AppointmentStatus, getattr(appt, "status"))
    if appt_status in (AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot modify a {appt_status.value} appointment"
        )

    updates = data.model_dump(exclude_unset=True)

    # If rescheduling, re-run availability check
    appt_scheduled_at_value: Any = getattr(appt, "scheduled_at")
    appt_scheduled_at = cast(datetime, appt_scheduled_at_value)
    appt_duration_minutes_value: Any = getattr(appt, "duration_minutes")
    appt_duration_minutes = cast(int, appt_duration_minutes_value)

    new_time_value: Any = updates.get("scheduled_at", appt_scheduled_at)
    new_time = cast(datetime, new_time_value)
    new_duration_value: Any = updates.get("duration_minutes", appt_duration_minutes)
    new_duration = cast(int, new_duration_value)
    appt_doctor_id_value: Any = getattr(appt, "doctor_id")
    appt_doctor_id = cast(int, appt_doctor_id_value)

    if "scheduled_at" in updates or "duration_minutes" in updates:
        _check_doctor_availability(
            db,
            doctor_id=appt_doctor_id,
            start_time=new_time,
            duration_minutes=new_duration,
            exclude_appointment_id=appointment_id,  # exclude self
        )

    for field, value in updates.items():
        setattr(appt, field, value)

    db.commit()
    db.refresh(appt)
    return appt


def cancel_appointment(db: Session, appointment_id: int) -> Appointment:
    """Convenience method — sets status to cancelled."""
    appt = get_appointment_by_id(db, appointment_id)
    appt_status = cast(AppointmentStatus, getattr(appt, "status"))

    if appt_status == AppointmentStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Appointment already cancelled")

    if appt_status == AppointmentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot cancel a completed appointment")

    appt.status = cast(Any, AppointmentStatus.CANCELLED.value)
    db.commit()
    db.refresh(appt)
    return appt
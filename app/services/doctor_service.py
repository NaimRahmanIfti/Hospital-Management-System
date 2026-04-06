# app/services/doctor_service.py

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.models.doctor import Doctor
from app.models.user import User, UserRole
from app.schemas.doctor import DoctorCreate, DoctorUpdate


def get_doctor_by_id(db: Session, doctor_id: int) -> Doctor:
    doctor = (
        db.query(Doctor)
        .options(joinedload(Doctor.user))
        .filter(Doctor.id == doctor_id)
        .first()
    )
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor {doctor_id} not found"
        )
    return doctor


def get_doctor_by_user_id(db: Session, user_id: int) -> Doctor | None:
    return db.query(Doctor).filter(Doctor.user_id == user_id).first()


def get_all_doctors(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    specialization: str | None = None,  # optional filter
) -> list[Doctor]:
    """
    List doctors with optional specialization filter.
    This is how you build filterable list endpoints — start broad,
    narrow down with .filter() only if the param was provided.
    """
    query = db.query(Doctor).options(joinedload(Doctor.user))

    if specialization:
        # ilike = case-insensitive LIKE
        # "%cardio%" matches "Cardiology", "cardiology", "CARDIOLOGY"
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))

    return query.offset(skip).limit(limit).all()


def create_doctor_profile(db: Session, data: DoctorCreate) -> Doctor:
    """Create a doctor profile. User must exist and have role='doctor'."""
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {data.user_id} not found")

    role_raw = user.role
    user_role: str
    if isinstance(role_raw, UserRole):
        user_role = role_raw.value
    elif isinstance(role_raw, str):
        user_role = role_raw
    else:
        user_role = str(role_raw)

    if str(user_role).lower() != "doctor":
        raise HTTPException(
            status_code=400,
            detail=f"User role is '{user_role}', expected 'doctor'"
        )

    # Check license_number is unique (enforced in DB too, but give a clear error)
    existing_license = db.query(Doctor).filter(
        Doctor.license_number == data.license_number
    ).first()
    if existing_license:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"License number '{data.license_number}' is already registered"
        )

    existing_profile = get_doctor_by_user_id(db, data.user_id)
    if existing_profile:
        raise HTTPException(status_code=409, detail="User already has a doctor profile")

    doctor = Doctor(**data.model_dump())
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


def update_doctor_profile(db: Session, doctor_id: int, data: DoctorUpdate) -> Doctor:
    doctor = get_doctor_by_id(db, doctor_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(doctor, field, value)
    db.commit()
    db.refresh(doctor)
    return doctor
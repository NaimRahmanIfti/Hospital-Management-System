# app/services/patient_service.py

from typing import cast

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.patient import PatientCreate, PatientUpdate
from app.core.services import BaseService


class PatientService(BaseService):
    """
    Service class for patient-related business logic.
    """

    def get_by_id(self, patient_id: int) -> Patient:
        """
        Load a patient WITH their user info in a single DB query.

        joinedload() is a SQLAlchemy technique called "eager loading".
        Without it:
            query 1 → fetch patient row
            query 2 → fetch user row (triggered when you access patient.user)
            query 3 → fetch appointments... (N+1 problem)
        With joinedload():
            query 1 → JOIN patients + users in one SQL call → done
        This is the N+1 query problem — a classic performance bug.
        """
        patient = (
            self._db.query(Patient)
            .options(joinedload(Patient.user))   # fetch user in same query
            .filter(Patient.id == patient_id)
            .first()
        )
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient {patient_id} not found"
            )
        return patient

    def get_by_user_id(self, user_id: int) -> Patient | None:
        """Returns the patient profile for a given user, or None."""
        return self._db.query(Patient).filter(Patient.user_id == user_id).first()

    def get_all(self, skip: int = 0, limit: int = 20) -> list[Patient]:
        return (
            self._db.query(Patient)
            .options(joinedload(Patient.user))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_profile(self, data: PatientCreate) -> Patient:
        """
        Create a patient profile for an existing user.

        Rules:
        - The user must exist
        - The user must have role='patient'
        - The user must not already have a patient profile
        """
        # Rule 1: user must exist
        user = self._db.query(User).filter(User.id == data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {data.user_id} not found"
            )

        # Rule 2: must be a patient role
        if cast(UserRole, user.role) != UserRole.PATIENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User has role '{user.role.value}', not 'patient'"
            )

        # Rule 3: no duplicate profile
        existing = self.get_by_user_id(data.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This user already has a patient profile"
            )

        patient = Patient(**data.model_dump())
        self._db.add(patient)
        self.commit()
        self.refresh(patient)
        return patient

    def update_profile(self, patient_id: int, data: PatientUpdate) -> Patient:
        patient = self.get_by_id(patient_id)

        # exclude_unset=True → only update fields the client actually sent
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(patient, field, value)

        self.commit()
        self.refresh(patient)
        return patient
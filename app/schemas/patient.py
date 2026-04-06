# app/schemas/patient.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date
import re


class PatientBase(BaseModel):
    date_of_birth:            Optional[date]    = None
    gender:                   Optional[str]     = Field(None, pattern="^(male|female|other)$")
    blood_type:               Optional[str]     = None
    phone:                    Optional[str]     = None
    address:                  Optional[str]     = None
    emergency_contact_name:   Optional[str]     = None
    emergency_contact_phone:  Optional[str]     = None

    @field_validator("blood_type")
    @classmethod
    def validate_blood_type(cls, v: Optional[str]) -> Optional[str]:
        # None is fine — it's optional
        if v is None:
            return v
        valid = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
        if v.upper() not in valid:
            raise ValueError(f"blood_type must be one of {valid}")
        return v.upper()

    @field_validator("phone", "emergency_contact_phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Strip spaces/dashes, check it's digits only
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        if not cleaned.isdigit() or len(cleaned) < 7:
            raise ValueError("Invalid phone number format")
        return v


class PatientCreate(PatientBase):
    # When creating a patient profile, we need the user_id
    # (the user account must already exist)
    user_id: int


class PatientUpdate(PatientBase):
    # All fields already Optional in PatientBase,
    # so PatientUpdate inherits that — user sends only changed fields
    pass


class PatientResponse(PatientBase):
    id: int
    user_id: int

    # Nested response — when we return a patient we also embed
    # their basic user info (name, email) so the client
    # doesn't need a second API call.
    # We use a forward reference string "UserResponse" to avoid
    # circular imports (user.py would import patient.py and vice versa)
    user: Optional["UserResponse"] = None

    model_config = {"from_attributes": True}


# Avoid circular import — import after class definition
from app.schemas.user import UserResponse  # noqa: E402
PatientResponse.model_rebuild()            # tell Pydantic to resolve the forward ref
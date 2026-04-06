# app/schemas/doctor.py

from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


class DoctorBase(BaseModel):
    specialization:   str            = Field(..., min_length=2, max_length=100)
    license_number:   str            = Field(..., min_length=4, max_length=50)
    consultation_fee: Decimal        = Field(default=Decimal("0.00"), ge=0)
    phone:            Optional[str]  = None
    department_id:    Optional[int]  = None


class DoctorCreate(DoctorBase):
    user_id: int


class DoctorUpdate(BaseModel):
    # All optional for partial updates
    specialization:   Optional[str]     = None
    consultation_fee: Optional[Decimal] = Field(None, ge=0)
    phone:            Optional[str]     = None
    department_id:    Optional[int]     = None


class DoctorResponse(DoctorBase):
    id: int
    user_id: int
    user: Optional["UserResponse"] = None

    model_config = {"from_attributes": True}


from app.schemas.user import UserResponse  # noqa: E402
DoctorResponse.model_rebuild()
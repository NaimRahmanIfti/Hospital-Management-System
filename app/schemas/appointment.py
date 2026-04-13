# app/schemas/appointment.py

from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime
from app.models.appointment import AppointmentStatus


class AppointmentBase(BaseModel):
    patient_id:       int
    doctor_id:        int
    room_id:          Optional[int]  = None
    scheduled_at:     datetime       = Field(..., description="ISO format: 2024-03-15T10:30:00")
    duration_minutes: int            = Field(default=30, ge=15, le=240)
    reason:           Optional[str]  = None


class AppointmentCreate(AppointmentBase):

    # model_validator runs after ALL fields are set.
    # Use it when validation needs to look at multiple fields together.
    # Here: we need both 'scheduled_at' to validate it.
    @model_validator(mode="after")
    def appointment_must_be_in_future(self) -> "AppointmentCreate":
        if self.scheduled_at.replace(tzinfo=None) <= datetime.now():
            raise ValueError("Appointment must be scheduled in the future")
        return self


class AppointmentUpdate(BaseModel):
    # Only these fields are editable after booking
    scheduled_at:     Optional[datetime] = None
    duration_minutes: Optional[int]      = Field(None, ge=15, le=240)
    room_id:          Optional[int]      = None
    status:           Optional[AppointmentStatus] = None
    notes:            Optional[str]      = None
    reason:           Optional[str]      = None

    @model_validator(mode="after")
    def future_if_rescheduling(self) -> "AppointmentUpdate":
        if self.scheduled_at and self.scheduled_at <= datetime.now():
            raise ValueError("Rescheduled time must be in the future")
        return self


class AppointmentResponse(AppointmentBase):
    id:     int
    status: AppointmentStatus
    notes:  Optional[str] = None

    # Nested: embed patient + doctor name so client has everything in one call
    patient_name: Optional[str] = None
    doctor_name:  Optional[str] = None

    model_config = {"from_attributes": True}
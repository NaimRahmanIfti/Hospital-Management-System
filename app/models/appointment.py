# app/models/appointment.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from app.core.db import Base
import enum


class AppointmentStatus(str, enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    no_show   = "no_show"


class Appointment(Base):
    __tablename__ = "appointments"

    id               = Column(Integer, primary_key=True, index=True)
    patient_id       = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id        = Column(Integer, ForeignKey("doctors.id"),  nullable=False)
    room_id          = Column(Integer, ForeignKey("rooms.id"),    nullable=True)
    scheduled_at     = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30)
    status           = Column(Enum(AppointmentStatus), default=AppointmentStatus.scheduled)
    reason           = Column(Text, nullable=True)
    notes            = Column(Text, nullable=True)

    patient        = relationship("Patient",       back_populates="appointments")
    doctor         = relationship("Doctor",        back_populates="appointments")
    room           = relationship("Room",          back_populates="appointments")
    medical_record = relationship("MedicalRecord", back_populates="appointment", uselist=False)
    invoice        = relationship("Invoice",       back_populates="appointment", uselist=False)

    def __repr__(self):
        return f"<Appointment id={self.id} status={self.status}>"
# app/models/medical_record.py

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id             = Column(Integer, primary_key=True, index=True)
    patient_id     = Column(Integer, ForeignKey("patients.id"),     nullable=False)
    doctor_id      = Column(Integer, ForeignKey("doctors.id"),      nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    diagnosis      = Column(Text, nullable=True)
    symptoms       = Column(Text, nullable=True)
    treatment      = Column(Text, nullable=True)
    follow_up_date = Column(DateTime, nullable=True)

    # ALL FOUR relationships must be here
    patient       = relationship("Patient",     back_populates="medical_records")
    doctor        = relationship("Doctor",      back_populates="medical_records")
    appointment   = relationship("Appointment", back_populates="medical_record")
    prescriptions = relationship("Prescription", back_populates="medical_record", cascade="all, delete-orphan")
    lab_results   = relationship("LabResult",    back_populates="medical_record", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MedicalRecord id={self.id} patient_id={self.patient_id}>"
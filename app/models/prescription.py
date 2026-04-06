# app/models/prescription.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base


class Prescription(Base):
    __tablename__ = "prescriptions"

    id                = Column(Integer, primary_key=True, index=True)
    medical_record_id = Column(Integer, ForeignKey("medical_records.id"), nullable=False)
    doctor_id         = Column(Integer, ForeignKey("doctors.id"),         nullable=False)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())
    medication_name   = Column(String(200), nullable=False)
    dosage            = Column(String(100), nullable=False)
    frequency         = Column(String(100), nullable=False)
    duration          = Column(String(100), nullable=True)
    instructions      = Column(Text, nullable=True)

    medical_record = relationship("MedicalRecord", back_populates="prescriptions")
    doctor         = relationship("Doctor",         back_populates="prescriptions")

    def __repr__(self):
        return f"<Prescription id={self.id} medication={self.medication_name}>"
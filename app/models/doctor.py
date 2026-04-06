# app/models/doctor.py

from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.core.db import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    specialization   = Column(String(100), nullable=False)
    license_number   = Column(String(50), unique=True, nullable=False)
    consultation_fee = Column(Numeric(10, 2), default=0.00)
    phone            = Column(String(20), nullable=True)
    department_id    = Column(Integer, ForeignKey("departments.id"), nullable=True)

    user            = relationship("User",          back_populates="doctor_profile")
    department      = relationship("Department",    back_populates="doctors")
    appointments    = relationship("Appointment",   back_populates="doctor")
    medical_records = relationship("MedicalRecord", back_populates="doctor")
    prescriptions   = relationship("Prescription",  back_populates="doctor")

    def __repr__(self):
        return f"<Doctor id={self.id} specialization={self.specialization}>"
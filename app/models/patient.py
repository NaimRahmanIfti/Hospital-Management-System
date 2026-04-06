# app/models/patient.py

from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base


class Patient(Base):
    __tablename__ = "patients"

    id                      = Column(Integer, primary_key=True, index=True)
    user_id                 = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    date_of_birth           = Column(Date, nullable=True)
    gender                  = Column(String(10), nullable=True)
    blood_type              = Column(String(5), nullable=True)
    phone                   = Column(String(20), nullable=True)
    address                 = Column(String(255), nullable=True)
    emergency_contact_name  = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)

    user            = relationship("User",          back_populates="patient_profile")
    appointments    = relationship("Appointment",   back_populates="patient", cascade="all, delete-orphan")
    medical_records = relationship("MedicalRecord", back_populates="patient", cascade="all, delete-orphan")
    invoices        = relationship("Invoice",       back_populates="patient", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Patient id={self.id} user_id={self.user_id}>"
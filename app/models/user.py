# app/models/user.py

from sqlalchemy import Column, Integer, String, Boolean, Enum
from sqlalchemy.orm import relationship
from app.core.db import Base
import enum


class UserRole(str, enum.Enum):
    admin   = "admin"
    doctor  = "doctor"
    patient = "patient"


class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    full_name       = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role            = Column(Enum(UserRole), nullable=False)
    is_active       = Column(Boolean, default=True, nullable=False)

    patient_profile = relationship("Patient", back_populates="user", uselist=False)
    doctor_profile  = relationship("Doctor",  back_populates="user", uselist=False)

    @property
    def display_name(self) -> str:
        return f"{self.full_name} ({self.role.value})"

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.admin

    @property
    def is_doctor(self) -> bool:
        return self.role == UserRole.doctor

    @property
    def is_patient(self) -> bool:
        return self.role == UserRole.patient

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"
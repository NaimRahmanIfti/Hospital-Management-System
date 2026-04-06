# app/models/department.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.db import Base


class Department(Base):
    __tablename__ = "departments"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    location    = Column(String(100), nullable=True)

    doctors = relationship("Doctor", back_populates="department")
    rooms   = relationship("Room",   back_populates="department")

    def __repr__(self):
        return f"<Department id={self.id} name={self.name}>"
# app/models/lab_result.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base
import enum


class LabStatus(str, enum.Enum):
    pending   = "pending"
    completed = "completed"
    cancelled = "cancelled"


class LabResult(Base):
    __tablename__ = "lab_results"

    id                = Column(Integer, primary_key=True, index=True)
    medical_record_id = Column(Integer, ForeignKey("medical_records.id"), nullable=False)
    test_name         = Column(String(200), nullable=False)
    test_code         = Column(String(50),  nullable=True)
    status            = Column(Enum(LabStatus), default=LabStatus.pending)
    ordered_at        = Column(DateTime(timezone=True), server_default=func.now())
    completed_at      = Column(DateTime(timezone=True), nullable=True)
    result_value      = Column(Text, nullable=True)
    normal_range      = Column(String(100), nullable=True)
    notes             = Column(Text, nullable=True)

    medical_record = relationship("MedicalRecord", back_populates="lab_results")

    def __repr__(self):
        return f"<LabResult id={self.id} test={self.test_name} status={self.status}>"
# app/models/document.py
#
# A MedicalDocument row is the database's "index card" for a file.
# The FILE (PDF, image) lives in S3. This row stores facts ABOUT the file:
#
#   medical_documents table             S3 bucket
#   ───────────────────────             ─────────────────────────────
#   id = 7                              patients/42/3f9a...c1.pdf  ◄── the bytes
#   patient_id = 42
#   storage_key = "patients/42/3f9a...c1.pdf"  ── points to ──┘
#   original_filename = "blood_test.pdf"
#   content_type = "application/pdf"
#   size_bytes = 184233
#
# WHY keep original_filename separate from storage_key?
# The user's filename is untrusted text ("../../hack.exe", emoji, spaces).
# We store it only for display. The real key is one WE generate (a UUID),
# so it's always safe and two "report.pdf" uploads never overwrite each other.

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db import Base


class MedicalDocument(Base):
    __tablename__ = "medical_documents"

    id = Column(Integer, primary_key=True, index=True)

    # Whose document is it? index=True → fast "all documents for patient 42".
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)

    # Optional: attach the file to a specific visit's medical record.
    medical_record_id = Column(Integer, ForeignKey("medical_records.id"), nullable=True)

    # Who uploaded it (an audit trail: in healthcare you must know who did what).
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    storage_key = Column(String(500), unique=True, nullable=False)
    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # One-directional relationships: we can do document.patient, but we did
    # NOT add a "documents" list to Patient. That keeps the existing models
    # untouched. You can add back_populates later if you need patient.documents.
    patient = relationship("Patient")
    uploaded_by = relationship("User")

    def __repr__(self):
        return f"<MedicalDocument id={self.id} patient_id={self.patient_id} key={self.storage_key}>"

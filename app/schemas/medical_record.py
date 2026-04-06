# app/schemas/medical_record.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── Medical Record ────────────────────────────────────────────────
class MedicalRecordBase(BaseModel):
    patient_id:     int
    doctor_id:      int
    appointment_id: Optional[int] = None
    diagnosis:      Optional[str] = None
    symptoms:       Optional[str] = None
    treatment:      Optional[str] = None
    follow_up_date: Optional[datetime] = None


class MedicalRecordCreate(MedicalRecordBase):
    pass


class MedicalRecordUpdate(BaseModel):
    diagnosis:      Optional[str]      = None
    symptoms:       Optional[str]      = None
    treatment:      Optional[str]      = None
    follow_up_date: Optional[datetime] = None


class MedicalRecordResponse(MedicalRecordBase):
    id:         int
    created_at: datetime

    # Embed the lists so the client gets everything in one response
    # List["PrescriptionResponse"] — forward ref, resolved below
    prescriptions: List["PrescriptionResponse"] = []
    lab_results:   List["LabResultResponse"]    = []

    model_config = {"from_attributes": True}


# ── Prescription ──────────────────────────────────────────────────
class PrescriptionBase(BaseModel):
    medical_record_id: int
    doctor_id:         int
    medication_name:   str = Field(..., min_length=1, max_length=200)
    dosage:            str = Field(..., min_length=1, max_length=100)
    frequency:         str = Field(..., min_length=1, max_length=100)
    duration:          Optional[str] = None
    instructions:      Optional[str] = None


class PrescriptionCreate(PrescriptionBase):
    pass


class PrescriptionUpdate(BaseModel):
    dosage:       Optional[str] = None
    frequency:    Optional[str] = None
    duration:     Optional[str] = None
    instructions: Optional[str] = None


class PrescriptionResponse(PrescriptionBase):
    id:         int
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Lab Result ────────────────────────────────────────────────────
class LabResultBase(BaseModel):
    medical_record_id: int
    test_name:         str = Field(..., min_length=1, max_length=200)
    test_code:         Optional[str] = None


class LabResultCreate(LabResultBase):
    pass


class LabResultUpdate(BaseModel):
    status:       Optional[str] = None
    result_value: Optional[str] = None
    normal_range: Optional[str] = None
    notes:        Optional[str] = None


class LabResultResponse(LabResultBase):
    id:           int
    status:       Optional[str]      = None
    result_value: Optional[str]      = None
    normal_range: Optional[str]      = None
    ordered_at:   datetime
    completed_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# Resolve forward references now that all classes are defined
MedicalRecordResponse.model_rebuild()
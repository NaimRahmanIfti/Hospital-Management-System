# app/services/medical_record_service.py

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.models.medical_record import MedicalRecord
from app.models.prescription import Prescription
from app.models.lab_result import LabResult, LabStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.schemas.medical_record import (
    MedicalRecordCreate, MedicalRecordUpdate,
    PrescriptionCreate, PrescriptionUpdate,
    LabResultCreate, LabResultUpdate,
)
from app.core.services import BaseService
from datetime import datetime, timezone


class MedicalRecordService(BaseService):
    """
    Service class for medical record-related business logic.
    """

    def _load_record_or_404(self, record_id: int) -> MedicalRecord:
        record = (
            self._db.query(MedicalRecord)
            .options(
                joinedload(MedicalRecord.patient).joinedload(Patient.user),
                joinedload(MedicalRecord.doctor).joinedload(Doctor.user),
                joinedload(MedicalRecord.prescriptions),
                joinedload(MedicalRecord.lab_results),
            )
            .filter(MedicalRecord.id == record_id)
            .first()
        )
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medical record {record_id} not found"
            )
        return record

    def create_record(
        self,
        data: MedicalRecordCreate,
        requesting_doctor_id: int,
    ) -> MedicalRecord:
        patient = self._db.query(Patient).filter(Patient.id == data.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {data.patient_id} not found")

        doctor = self._db.query(Doctor).filter(Doctor.id == data.doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=404, detail=f"Doctor {data.doctor_id} not found")

        if data.appointment_id:
            appt = self._db.query(Appointment).filter(Appointment.id == data.appointment_id).first()
            if not appt:
                raise HTTPException(status_code=404, detail=f"Appointment {data.appointment_id} not found")
            if appt.doctor_id != requesting_doctor_id:
                raise HTTPException(status_code=403, detail="You can only create records for your own appointments")
            if appt.patient_id != data.patient_id:
                raise HTTPException(status_code=400, detail="Patient does not match the appointment's patient")

        if data.appointment_id:
            existing = self._db.query(MedicalRecord).filter(
                MedicalRecord.appointment_id == data.appointment_id
            ).first()
            if existing:
                raise HTTPException(status_code=409, detail=f"A medical record already exists for appointment {data.appointment_id}")

        record = MedicalRecord(**data.model_dump())
        self._db.add(record)
        self.commit()
        self.refresh(record)
        return self._load_record_or_404(record.id)

    def get_record(self, record_id: int) -> MedicalRecord:
        return self._load_record_or_404(record_id)

    def get_records_for_patient(self, patient_id: int) -> list[MedicalRecord]:
        return (
            self._db.query(MedicalRecord)
            .options(
                joinedload(MedicalRecord.doctor).joinedload(Doctor.user),
                joinedload(MedicalRecord.prescriptions),
                joinedload(MedicalRecord.lab_results),
            )
            .filter(MedicalRecord.patient_id == patient_id)
            .order_by(MedicalRecord.created_at.desc())
            .all()
        )

    def get_records_by_doctor(self, doctor_id: int) -> list[MedicalRecord]:
        return (
            self._db.query(MedicalRecord)
            .options(
                joinedload(MedicalRecord.patient).joinedload(Patient.user),
                joinedload(MedicalRecord.prescriptions),
                joinedload(MedicalRecord.lab_results),
            )
            .filter(MedicalRecord.doctor_id == doctor_id)
            .order_by(MedicalRecord.created_at.desc())
            .all()
        )

    def update_record(
        self,
        record_id: int,
        data: MedicalRecordUpdate,
        requesting_doctor_id: int,
    ) -> MedicalRecord:
        record = self._load_record_or_404(record_id)
        if record.doctor_id != requesting_doctor_id:
            raise HTTPException(status_code=403, detail="You can only update records you created")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(record, field, value)
        self.commit()
        self.refresh(record)
        return self._load_record_or_404(record_id)

    def add_prescription(
        self,
        data: PrescriptionCreate,
        requesting_doctor_id: int,
    ) -> Prescription:
        record = self._load_record_or_404(data.medical_record_id)
        if record.doctor_id != requesting_doctor_id:
            raise HTTPException(status_code=403, detail="You can only prescribe on records you created")
        prescription = Prescription(**data.model_dump())
        self._db.add(prescription)
        self.commit()
        self.refresh(prescription)
        return prescription

    def update_prescription(
        self,
        prescription_id: int,
        data: PrescriptionUpdate,
        requesting_doctor_id: int,
    ) -> Prescription:
        rx = self._db.query(Prescription).filter(Prescription.id == prescription_id).first()
        if not rx:
            raise HTTPException(status_code=404, detail=f"Prescription {prescription_id} not found")
        record = self._load_record_or_404(rx.medical_record_id)
        if record.doctor_id != requesting_doctor_id:
            raise HTTPException(status_code=403, detail="Access denied")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(rx, field, value)
        self.commit()
        self.refresh(rx)
        return rx

    def order_lab_test(
        self,
        data: LabResultCreate,
        requesting_doctor_id: int,
    ) -> LabResult:
        record = self._load_record_or_404(data.medical_record_id)
        if record.doctor_id != requesting_doctor_id:
            raise HTTPException(status_code=403, detail="You can only order tests on records you created")
        lab = LabResult(**data.model_dump())
        self._db.add(lab)
        self.commit()
        self.refresh(lab)
        return lab

    def update_lab_result(
        self,
        lab_id: int,
        data: LabResultUpdate,
        requesting_doctor_id: int,
    ) -> LabResult:
        lab = self._db.query(LabResult).filter(LabResult.id == lab_id).first()
        if not lab:
            raise HTTPException(status_code=404, detail=f"Lab result {lab_id} not found")
        record = self._load_record_or_404(lab.medical_record_id)
        if record.doctor_id != requesting_doctor_id:
            raise HTTPException(status_code=403, detail="Access denied")
        updates = data.model_dump(exclude_unset=True)
        if updates.get("status") == LabStatus.completed and not lab.completed_at:
            updates["completed_at"] = datetime.now(timezone.utc)
        for field, value in updates.items():
            setattr(lab, field, value)
        self.commit()
        self.refresh(lab)
        return lab
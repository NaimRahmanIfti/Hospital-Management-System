# app/routers/documents.py
#
# Endpoints for medical documents (lab reports, scans, prescriptions as PDF/image).
#
#   POST   /documents/patient/{patient_id}   upload a file
#   GET    /documents/patient/{patient_id}   list a patient's files
#   GET    /documents/{id}/download          get a temporary download link
#   GET    /documents/{id}/content           stream the file (local dev only)
#   DELETE /documents/{id}                   delete (admin or the uploader)
#
# THE UPLOAD FLOW
#
#   Browser ──multipart/form-data──► FastAPI ──put_object──► S3 bucket
#                                       │
#                                       └── INSERT row ──► PostgreSQL (RDS)
#
# THE DOWNLOAD FLOW (why the bucket can stay private)
#
#   Browser ──GET /documents/7/download──► FastAPI: "may this user see doc 7?"
#                                             │ yes
#   Browser ◄──{ url: presigned link }────────┘
#   Browser ──GET presigned link──────────► S3 (checks signature + expiry)

import uuid
from typing import List, Optional, cast

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.dependencies import get_current_active_user
from app.core.storage import StorageBackend, get_storage
from app.models.document import MedicalDocument
from app.models.medical_record import MedicalRecord
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.document import DocumentResponse, DownloadLink
from app.services import patient_service

router = APIRouter(prefix="/documents", tags=["Documents"])


# Allowed file types → their file extension and "magic bytes".
# WHY magic bytes? The Content-Type header comes from the client, so an
# attacker can send an .exe and claim "application/pdf". Real files start
# with a fixed signature (every PDF begins with "%PDF"), so we check that.
ALLOWED_TYPES = {
    "application/pdf": (".pdf", [b"%PDF"]),
    "image/png": (".png", [b"\x89PNG\r\n\x1a\n"]),
    "image/jpeg": (".jpg", [b"\xff\xd8\xff"]),
}


# ── Access-control helpers ────────────────────────────────────────
def _is(user: User, role: UserRole) -> bool:
    return cast(UserRole, user.role) == role


def _check_patient_access(db: Session, user: User, patient_id: int) -> None:
    """
    Same rule as medical records:
      patient → only their OWN files
      doctor / admin → any patient's files (they treat the patient)
    """
    if _is(user, UserRole.patient):
        own = patient_service.get_patient_by_user_id(db, cast(int, user.id))
        if own is None or cast(int, own.id) != patient_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def _get_document_or_404(db: Session, document_id: int) -> MedicalDocument:
    doc = db.get(MedicalDocument, document_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


# ── POST /documents/patient/{patient_id} ──────────────────────────
@router.post(
    "/patient/{patient_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    patient_id: int,
    # File(...) and Form(...) mean this endpoint takes multipart/form-data
    # (the format browsers use for file uploads), not JSON.
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    medical_record_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    # Depends(get_storage) instead of calling get_storage() directly:
    # tests can swap in a fake storage with app.dependency_overrides.
    storage: StorageBackend = Depends(get_storage),
):
    _check_patient_access(db, current_user, patient_id)

    if db.get(Patient, patient_id) is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    if medical_record_id is not None:
        record = db.get(MedicalRecord, medical_record_id)
        # A file must not be attached to SOMEONE ELSE's record.
        if record is None or cast(int, record.patient_id) != patient_id:
            raise HTTPException(status_code=400, detail="Medical record not found for this patient")

    # 1. Type check (header)
    content_type = file.content_type or ""
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF, PNG and JPEG files are allowed",
        )
    extension, signatures = ALLOWED_TYPES[content_type]

    # 2. Size check. Read at most MAX+1 bytes: if we got more than MAX,
    #    the file is too big, and we never loaded a 2 GB upload into memory.
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    data = file.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File is larger than {settings.MAX_UPLOAD_MB} MB",
        )
    if not data:
        raise HTTPException(status_code=400, detail="File is empty")

    # 3. Content check (magic bytes)
    if not any(data.startswith(sig) for sig in signatures):
        raise HTTPException(status_code=400, detail="File content does not match its type")

    # 4. Build OUR key. uuid4() = random 128-bit id, practically never repeats.
    #    Prefixing with patients/{id}/ groups each patient's files together.
    key = f"patients/{patient_id}/{uuid.uuid4().hex}{extension}"

    # 5. Upload the file FIRST, then write the DB row.
    #    If the upload fails → no row is written, nothing points at a missing file.
    #    If the DB write fails → we delete the uploaded file (cleanup), then re-raise.
    storage.save(key, data, content_type)
    doc = MedicalDocument(
        patient_id=patient_id,
        medical_record_id=medical_record_id,
        uploaded_by_id=current_user.id,
        storage_key=key,
        original_filename=(file.filename or "document")[:255],
        content_type=content_type,
        size_bytes=len(data),
        description=description,
    )
    try:
        db.add(doc)
        db.commit()
    except Exception:
        db.rollback()
        storage.delete(key)
        raise
    db.refresh(doc)
    return doc


# ── GET /documents/patient/{patient_id} ───────────────────────────
@router.get("/patient/{patient_id}", response_model=List[DocumentResponse])
def list_patient_documents(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    _check_patient_access(db, current_user, patient_id)
    return (
        db.query(MedicalDocument)
        .filter(MedicalDocument.patient_id == patient_id)
        .order_by(MedicalDocument.created_at.desc())
        .all()
    )


# ── GET /documents/{id}/download ──────────────────────────────────
@router.get("/{document_id}/download", response_model=DownloadLink)
def get_download_link(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    storage: StorageBackend = Depends(get_storage),
):
    doc = _get_document_or_404(db, document_id)
    _check_patient_access(db, current_user, cast(int, doc.patient_id))

    url = storage.get_download_url(cast(str, doc.storage_key), cast(str, doc.original_filename))
    if url is None:
        # Local storage: point at our own streaming endpoint instead.
        return DownloadLink(url=f"/documents/{doc.id}/content", expires_in=0)
    return DownloadLink(url=url, expires_in=settings.S3_PRESIGNED_URL_EXPIRE_SECONDS)


# ── GET /documents/{id}/content ───────────────────────────────────
@router.get("/{document_id}/content")
def get_document_content(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    storage: StorageBackend = Depends(get_storage),
):
    """Streams the file through the API. Used in local dev (S3 uses presigned links)."""
    doc = _get_document_or_404(db, document_id)
    _check_patient_access(db, current_user, cast(int, doc.patient_id))
    data = storage.load(cast(str, doc.storage_key))
    safe_name = cast(str, doc.original_filename).replace('"', "")
    return Response(
        content=data,
        media_type=cast(str, doc.content_type),
        headers={"Content-Disposition": f'attachment; filename="{safe_name}"'},
    )


# ── DELETE /documents/{id} ────────────────────────────────────────
@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    storage: StorageBackend = Depends(get_storage),
):
    doc = _get_document_or_404(db, document_id)
    if not _is(current_user, UserRole.admin) and doc.uploaded_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the uploader or an admin can delete")

    key = cast(str, doc.storage_key)
    db.delete(doc)
    db.commit()
    # Delete the file AFTER the row is gone. If this step fails, we're left
    # with an orphan file (harmless, can be cleaned up), never a row that
    # points to a missing file.
    storage.delete(key)

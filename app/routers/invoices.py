# app/routers/invoices.py

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, cast
from app.core.db import get_db
from app.core.dependencies import get_current_active_user, require_admin
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceResponse
from app.services import invoice_service, patient_service
from app.models.user import User, UserRole

router = APIRouter(prefix="/invoices", tags=["Invoices"])


def _is_patient(user: User) -> bool:
    return cast(UserRole, user.role) == UserRole.patient


def _parse_payment_status(payment_status: Optional[str]) -> Optional[str]:
    if payment_status is None:
        return None

    allowed_statuses = {"pending", "paid", "partial", "overdue", "waived"}
    if payment_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status: '{payment_status}'. Allowed: {sorted(allowed_statuses)}"
        )
    return payment_status


# ── POST /invoices ────────────────────────────────────────────────
@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create an invoice with line items.
    Totals are computed server-side — any totals sent by the client are ignored.
    Admin and doctors can create invoices; patients cannot.
    """
    if _is_patient(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patients cannot create invoices"
        )
    return invoice_service.create_invoice(db, data)


# ── GET /invoices (admin + doctor) ───────────────────────────────
@router.get("/", response_model=List[InvoiceResponse])
def list_all_invoices(
    skip: int = 0,
    limit: int = 20,
    payment_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all invoices. Admin and doctors only. Filter by payment status."""
    if _is_patient(current_user):
        raise HTTPException(status_code=403, detail="Patients cannot list all invoices")
    status_filter = _parse_payment_status(payment_status)
    return invoice_service.get_all_invoices(db, skip, limit, status_filter)


# ── GET /invoices/my ──────────────────────────────────────────────
@router.get("/my", response_model=List[InvoiceResponse])
def get_my_invoices(
    payment_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[InvoiceResponse]:
    """
    Get invoices for the currently logged-in patient.
    Doctors and admins: use /invoices/patient/{id} instead.
    """
    if not _is_patient(current_user):
        raise HTTPException(
            status_code=400,
            detail="This endpoint is for patients. Admins: use /invoices/ or /invoices/patient/{id}"
        )

    user_id = cast(int, current_user.id)
    profile = patient_service.get_patient_by_user_id(db, user_id)
    if profile is None:
        return cast(List[InvoiceResponse], [])

    status_filter = _parse_payment_status(payment_status)
    patient_id = cast(int, profile.id)
    invoices = invoice_service.get_invoices_for_patient(db, patient_id, status_filter)
    return cast(List[InvoiceResponse], invoices)


# ── GET /invoices/patient/{patient_id} ───────────────────────────
@router.get("/patient/{patient_id}", response_model=List[InvoiceResponse])
def get_patient_invoices(
    patient_id: int,
    payment_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get all invoices for a specific patient.
    Patients can only access their own; admins can access anyone's.
    """
    if _is_patient(current_user):
        user_id = cast(int, current_user.id)
        own = patient_service.get_patient_by_user_id(db, user_id)
        if own is None:
            raise HTTPException(status_code=403, detail="Access denied")
        own_id = cast(int, own.id)
        if own_id != patient_id:
            raise HTTPException(status_code=403, detail="Access denied")

    status_filter = _parse_payment_status(payment_status)
    return invoice_service.get_invoices_for_patient(db, patient_id, status_filter)


# ── GET /invoices/{invoice_id} ────────────────────────────────────
@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    invoice = invoice_service.get_invoice(db, invoice_id)

    # Patients can only see their own invoices
    if _is_patient(current_user):
        user_id = cast(int, current_user.id)
        own = patient_service.get_patient_by_user_id(db, user_id)
        if own is None:
            raise HTTPException(status_code=403, detail="Access denied")
        own_id = cast(int, own.id)
        invoice_patient_id = cast(int, invoice.patient_id)
        if invoice_patient_id != own_id:
            raise HTTPException(status_code=403, detail="Access denied")

    return invoice


# ── PATCH /invoices/{invoice_id} ─────────────────────────────────
@router.patch("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: int,
    data: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update invoice — change payment status, apply discount, update due date.
    Doctors and admins only. Totals are recomputed if discount changes.
    """
    if _is_patient(current_user):
        from app.services import patient_service as ps
        from typing import cast as c
        from app.models.invoice import PaymentStatus as PS
        patient = ps.get_patient_by_user_id(db, c(int, current_user.id))
        if not patient:
            raise HTTPException(status_code=403, detail='Patient profile not found')
        inv = invoice_service.get_invoice(db, invoice_id)
        if c(int, inv.patient_id) != c(int, patient.id):
            raise HTTPException(status_code=403, detail='You can only pay your own invoices')
        if data.status not in [None, PS.paid]:
            raise HTTPException(status_code=403, detail='Patients can only mark invoices as paid')
    return invoice_service.update_invoice(db, invoice_id, data)
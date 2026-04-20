# app/services/invoice_service.py

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from decimal import Decimal, ROUND_HALF_UP
from typing import cast
from app.models.invoice import Invoice, InvoiceItem
from app.models.patient import Patient
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate
from app.core.services import BaseService


class InvoiceService:
    """
    Service class for invoice-related business logic.
    """
    def __init__(self, db):
        self._db = db

    def commit(self):
        self._db.commit()

    def refresh(self, obj):
        self._db.refresh(obj)



    # Tax rate — in a real system this would be configurable per location
    TAX_RATE = Decimal("0.08")   # 8%

    def _load_invoice_or_404(self, invoice_id: int) -> Invoice:
        invoice = (
            self._db.query(Invoice)
            .options(
                joinedload(Invoice.patient).joinedload(Patient.user),
                joinedload(Invoice.items),
            )
            .filter(Invoice.id == invoice_id)
            .first()
        )
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice {invoice_id} not found"
            )
        return invoice

    def _compute_totals(
        self,
        items: list[InvoiceItem],
        discount: Decimal = Decimal("0.00"),
    ) -> tuple[Decimal, Decimal, Decimal]:
        """
        Compute (subtotal, tax, total) from line items.

        WHY server-side?
        If the client sends totals, a malicious user could send:
            { subtotal: 0.01, total: 0.01 }
        and the DB would store $0.01 for a $500 procedure.
        Server always recomputes — client math is ignored.

        Returns: (subtotal, tax, total) as Decimal values.
        """
        subtotal = sum(
            (
                Decimal(str(item.unit_price)) * Decimal(str(item.quantity))
                for item in items
            ),
            Decimal("0.00"),
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Apply discount before tax (discount on pre-tax amount)
        discount_value = Decimal(str(discount))
        discounted = max(subtotal - discount_value, Decimal("0.00"))

        # Tax on discounted subtotal
        tax = (discounted * self.TAX_RATE).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        total = (discounted + tax).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return subtotal, tax, total

    def create_invoice(self, data: InvoiceCreate) -> Invoice:
        """
        Create an invoice with line items.

        Flow:
        1. Validate patient exists
        2. Check no existing unpaid invoice for this appointment
        3. Create Invoice row
        4. Create InvoiceItem rows
        5. Compute totals server-side and store them
        """
        # Step 1: patient must exist
        patient = self._db.query(Patient).filter(Patient.id == data.patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {data.patient_id} not found")

        # Step 2: no duplicate invoice for same appointment
        if data.appointment_id:
            existing = self._db.query(Invoice).filter(
                Invoice.appointment_id == data.appointment_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Invoice already exists for appointment {data.appointment_id} (invoice id={existing.id})"
                )

        # Step 3: create the Invoice header (totals are 0 for now, computed below)
        invoice = Invoice(
            patient_id=data.patient_id,
            appointment_id=data.appointment_id,
            notes=data.notes,
            subtotal=Decimal("0.00"),
            tax_rate=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("0.00"),
        )
        self._db.add(invoice)
        self._db.flush()   # flush sends the INSERT to get invoice.id WITHOUT committing
                     # We need invoice.id before creating InvoiceItems

        # Step 4: create line items
        # Why not use data.items directly?
        # data.items are Pydantic schemas — we need SQLAlchemy model objects
        db_items: list[InvoiceItem] = []
        for item_data in data.items:
            unit_price  = Decimal(str(item_data.unit_price))
            total_price = (unit_price * item_data.quantity).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            db_item = InvoiceItem(
                invoice_id=invoice.id,
                description=item_data.description,
                quantity=item_data.quantity,
                unit_price=unit_price,
                total_price=total_price,
            )
            self._db.add(db_item)
            db_items.append(db_item)

        self._db.flush()   # flush items so we can compute from them

        # Step 5: compute totals server-side and update the Invoice
        subtotal, tax, total = self._compute_totals(db_items)
        setattr(invoice, "subtotal", subtotal)
        setattr(invoice, "tax_amount", tax)
        setattr(invoice, "total_amount", total)

        self.commit()
        self.refresh(invoice)
        invoice_id = cast(int, invoice.id)
        return self._load_invoice_or_404(invoice_id)

    def get_invoice(self, invoice_id: int) -> Invoice:
        return self._load_invoice_or_404(invoice_id)

    def get_invoices_for_patient(
        self,
        patient_id: int,
        status_filter: str | None = None,
    ) -> list[Invoice]:
        query = (
            self._db.query(Invoice)
            .options(joinedload(Invoice.items))
            .filter(Invoice.patient_id == patient_id)
        )
        if status_filter:
            query = query.filter(Invoice.status == status_filter)
        return query.order_by(Invoice.created_at.desc()).all()

    def get_all_invoices(
        self,
        skip: int = 0,
        limit: int = 20,
        status_filter: str | None = None,
    ) -> list[Invoice]:
        query = (
            self._db.query(Invoice)
            .options(
                joinedload(Invoice.patient).joinedload(Patient.user),
                joinedload(Invoice.items),
            )
        )
        if status_filter:
            query = query.filter(Invoice.status == status_filter)
        return query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()

    def update_invoice(
        self,
        invoice_id: int,
        data: InvoiceUpdate,
    ) -> Invoice:
        """
        Update invoice metadata (payment status, discount, due date).
        Totals are recomputed if discount changes.
        """
        invoice = self._load_invoice_or_404(invoice_id)

        # Cannot modify a paid invoice
        current_payment_status = getattr(invoice, "status", None)
        current_payment_status_value = str(current_payment_status) if current_payment_status else None
        if current_payment_status_value and "paid" in str(current_payment_status_value).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify a paid invoice"
            )

        updates = data.model_dump(exclude_unset=True)

        # If discount changes, recompute all totals
        if "discount" in updates:
            new_discount = Decimal(str(updates["discount"]))
            subtotal, tax, total = self._compute_totals(invoice.items, new_discount)
            pass  # discount not in model
            setattr(invoice, "subtotal", subtotal)
            setattr(invoice, "tax_amount", tax)
            setattr(invoice, "total_amount", total)
            # Remove from updates dict — already applied
            updates.pop("discount")

        for field, value in updates.items():
            setattr(invoice, field, value)

        self.commit()
        self.refresh(invoice)
        return self._load_invoice_or_404(invoice_id)

# Function wrappers for router compatibility


# Function wrappers for router compatibility
def get_all_invoices(db, skip=0, limit=100, status_filter=None):
    return InvoiceService(db).get_all_invoices(skip, limit, status_filter)

def get_invoice(db, invoice_id):
    return InvoiceService(db).get_invoice(invoice_id)

def get_invoices_for_patient(db, patient_id):
    return InvoiceService(db).get_invoices_for_patient(patient_id)

def create_invoice(db, data):
    return InvoiceService(db).create_invoice(data)

def update_invoice(db, invoice_id, data):
    return InvoiceService(db).update_invoice(invoice_id, data)

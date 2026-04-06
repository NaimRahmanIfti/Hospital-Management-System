# app/schemas/invoice.py

from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.models.invoice import PaymentStatus


# ── Invoice Item ──────────────────────────────────────────────────
class InvoiceItemBase(BaseModel):
    description: str     = Field(..., min_length=1, max_length=255)
    quantity:    int     = Field(default=1, ge=1)
    unit_price:  Decimal = Field(..., ge=0)

    # Computed field: quantity * unit_price
    # model_validator ensures total_price is always correct
    # even if the client sends a wrong value
    total_price: Optional[Decimal] = None

    @model_validator(mode="after")
    def compute_total(self) -> "InvoiceItemBase":
        self.total_price = self.unit_price * self.quantity
        return self


class InvoiceItemCreate(InvoiceItemBase):
    pass   # invoice_id is set by the service, not the client


class InvoiceItemResponse(InvoiceItemBase):
    id:          int
    invoice_id:  int
    model_config = {"from_attributes": True}


# ── Invoice ───────────────────────────────────────────────────────
class InvoiceBase(BaseModel):
    patient_id:    int
    appointment_id: Optional[int]    = None
    due_date:      Optional[datetime] = None
    notes:         Optional[str]      = None


class InvoiceCreate(InvoiceBase):
    # Client sends the line items along with the invoice
    items: List[InvoiceItemCreate] = Field(..., min_length=1)

    # Pydantic v2 notation for Field constraint
    # min_length=1 means at least one item required


class InvoiceUpdate(BaseModel):
    status:         Optional[PaymentStatus] = None
    due_date:       Optional[datetime]      = None
    notes:          Optional[str]           = None
    discount:       Optional[Decimal]       = Field(None, ge=0)


class InvoiceResponse(InvoiceBase):
    id:             int
    created_at:     datetime
    subtotal:       Decimal
    tax_amount:     Decimal
    tax_rate:       Optional[Decimal] = None
    total_amount:   Decimal
    status:         PaymentStatus
    items:          List[InvoiceItemResponse] = []

    model_config = {"from_attributes": True}
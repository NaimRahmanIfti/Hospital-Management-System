# app/models/invoice.py

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.db import Base


class PaymentStatus(str, enum.Enum):
    pending  = "pending"
    paid     = "paid"
    partial  = "partial"
    overdue  = "overdue"
    waived   = "waived"
class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)

    # Which patient owes this money
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    # Which appointment generated this invoice
    appointment_id = Column(
        Integer, ForeignKey("appointments.id"), unique=True, nullable=True
    )

    # ── Financial Fields ──────────────────────────────────────────
    # Numeric(10, 2) = up to 10 digits, 2 decimal places (like 9999999.99)
    # ALWAYS use Numeric for money. Never Float. Float = floating point errors.
    subtotal = Column(Numeric(10, 2), default=0.00)   # Before tax
    tax_rate = Column(Numeric(5, 2), default=0.00)    # e.g. 8.50 means 8.5%
    tax_amount = Column(Numeric(10, 2), default=0.00) # Calculated: subtotal * tax_rate
    total_amount = Column(Numeric(10, 2), default=0.00) # subtotal + tax_amount

    status = Column(
        SqlEnum(PaymentStatus, name="paymentstatus"),
        default=PaymentStatus.pending,
        nullable=False,
    )

    # Free text for any notes on the invoice
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    paid_at = Column(DateTime, nullable=True)  # Set when status → PAID

    # ── Relationships ─────────────────────────────────────────────
    patient = relationship("Patient", back_populates="invoices")
    appointment = relationship("Appointment", back_populates="invoice")

    # Invoice has line items — e.g. "Consultation Fee: $100", "Lab Test: $50"
    items = relationship(
        "InvoiceItem", back_populates="invoice", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Invoice id={self.id} total={self.total_amount} status={self.status}>"


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)

    # What this line item is for
    description = Column(String(200), nullable=False)  # "Consultation Fee"
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)  # Price per unit
    total_price = Column(Numeric(10, 2), nullable=False)  # quantity * unit_price

    invoice = relationship("Invoice", back_populates="items")

    def __repr__(self):
        return f"<InvoiceItem desc={self.description} total={self.total_price}>"
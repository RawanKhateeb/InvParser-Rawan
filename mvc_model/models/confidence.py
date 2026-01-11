from typing import List, Optional
from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship, Session
from mvc_model.models.base import Base


class Confidence(Base):
    __tablename__ = "confidences"

    InvoiceId = Column(String, ForeignKey("invoices.InvoiceId"), primary_key=True)
    VendorName = Column(Float)
    InvoiceDate = Column(Float)
    BillingAddressRecipient = Column(Float)
    ShippingAddress = Column(Float)
    SubTotal = Column(Float)
    ShippingCost = Column(Float)
    InvoiceTotal = Column(Float)

    invoice = relationship("Invoice", back_populates="confidences")


def create_confidence(db: Session, confidence_data: dict) -> Confidence:
    confidence = Confidence(
        InvoiceId=confidence_data.get("InvoiceId"),
        VendorName=confidence_data.get("VendorName"),
        InvoiceDate=confidence_data.get("InvoiceDate"),
        BillingAddressRecipient=confidence_data.get("BillingAddressRecipient"),
        ShippingAddress=confidence_data.get("ShippingAddress"),
        SubTotal=confidence_data.get("SubTotal"),
        ShippingCost=confidence_data.get("ShippingCost"),
        InvoiceTotal=confidence_data.get("InvoiceTotal"),
    )
    db.add(confidence)
    db.commit()
    db.refresh
    return confidence


def get_confidence_by_invoice_id(db: Session, invoice_id: str) -> Optional[Confidence]:
    return db.query(Confidence).filter(Confidence.InvoiceId == invoice_id).first()


def get_confidences(db: Session, skip: int = 0, limit: int = 100) -> List[Confidence]:
    return db.query(Confidence).offset(skip).limit(limit).all()


def update_confidence(db: Session, invoice_id: str, update_data: dict) -> Optional[Confidence]:
    confidence = get_confidence_by_invoice_id(db, invoice_id)
    if not confidence:
        return None

    if "VendorName" in update_data:
        confidence.VendorName = update_data["VendorName"]
    if "InvoiceDate" in update_data:
        confidence.InvoiceDate = update_data["InvoiceDate"]
    if "BillingAddressRecipient" in update_data:
        confidence.BillingAddressRecipient = update_data["BillingAddressRecipient"]
    if "ShippingAddress" in update_data:
        confidence.ShippingAddress = update_data["ShippingAddress"]
    if "SubTotal" in update_data:
        confidence.SubTotal = update_data["SubTotal"]
    if "ShippingCost" in update_data:
        confidence.ShippingCost = update_data["ShippingCost"]
    if "InvoiceTotal" in update_data:
        confidence.InvoiceTotal = update_data["InvoiceTotal"]

    db.commit()
    db.refresh(confidence)
    return confidence


def delete_confidence(db: Session, invoice_id: str) -> bool:
    confidence = get_confidence_by_invoice_id(db, invoice_id)
    if not confidence:
        return False

    db.delete(confidence)
    db.commit()
    return True

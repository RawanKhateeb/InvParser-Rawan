# models.py
from typing import List, Optional
from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import  Session
from sqlalchemy import func

# All models inherit from this base class
from mvc_model.models.base import Base


class Invoice(Base):
    """
    Model for invoices table
    
    This replaces: CREATE TABLE invoices (...)
    """
    __tablename__ = 'invoices'
    
    InvoiceId = Column(String, primary_key=True)
    VendorName = Column(String)
    InvoiceDate = Column(String)
    BillingAddressRecipient = Column(String)
    ShippingAddress = Column(String)
    SubTotal = Column(Float)
    ShippingCost = Column(Float)
    InvoiceTotal = Column(Float)
    
    # Relationships
    confidences = relationship("Confidence", back_populates="invoice")
    items = relationship("Item", back_populates="invoice")

#---------------------------------CRUD-----------------------------------#
def create_invoice(db: Session, invoice_data: dict) -> Invoice:
    if not invoice_data:
        return None
    invoice= Invoice(
        InvoiceId=invoice_data.get("InvoiceId"),
        VendorName=invoice_data.get("VendorName"),
        InvoiceDate=invoice_data.get("InvoiceDate"),
        BillingAddressRecipient=invoice_data.get("BillingAddressRecipient"),
        ShippingAddress=invoice_data.get("ShippingAddress"),
        SubTotal=invoice_data.get("SubTotal"),
        ShippingCost=invoice_data.get("ShippingCost"),
        InvoiceTotal=invoice_data.get("InvoiceTotal"))
    db.add(invoice)
    db.commit()
    db.refresh
    return invoice


def get_invoice_by_id(db: Session, invoice_id: str) -> Optional[Invoice]:
    invoiceItem = db.query(Invoice).filter(Invoice.InvoiceId == invoice_id).first()
    return invoiceItem

def get_invoice_by_vendor_name(db: Session, vendor_name: str) -> List[Invoice]:
    invoices = db.query(Invoice).filter(Invoice.VendorName == vendor_name).all()
    return invoices

def get_invoices(db: Session) -> List[Invoice]:
    invoices = db.query(Invoice).all()
    return invoices


def update_invoice(db: Session, invoice_id: str, update_data: dict) -> Optional[Invoice]:
    invoice = get_invoice_by_id(db, invoice_id)
    if not invoice:
        return None

    if "VendorName" in update_data:
        invoice.VendorName = update_data["VendorName"]
    if "InvoiceDate" in update_data:
        invoice.InvoiceDate = update_data["InvoiceDate"]
    if "BillingAddressRecipient" in update_data:
        invoice.BillingAddressRecipient = update_data["BillingAddressRecipient"]
    if "ShippingAddress" in update_data:
        invoice.ShippingAddress = update_data["ShippingAddress"]
    if "SubTotal" in update_data:
        invoice.SubTotal = update_data["SubTotal"]
    if "ShippingCost" in update_data:
        invoice.ShippingCost = update_data["ShippingCost"]
    if "InvoiceTotal" in update_data:
        invoice.InvoiceTotal = update_data["InvoiceTotal"]

    db.commit()
    db.refresh(invoice)
    return invoice


def delete_invoice(db: Session, invoice_id: str) -> bool:
    invoice = get_invoice_by_id(db, invoice_id)
    if  invoice:
        db.delete(invoice)
        db.commit()
        return True
    return False
        
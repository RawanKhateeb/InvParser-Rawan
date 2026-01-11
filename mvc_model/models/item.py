# models/item.py
from typing import List, Optional
from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship, Session  # ✅ SQLAlchemy Session 
from mvc_model.models.base import Base
from mvc_model.models.invoice import get_invoice_by_id


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    InvoiceId = Column(String, ForeignKey("invoices.InvoiceId"))
    Description = Column(String)
    Name = Column(String)
    Quantity = Column(Float)
    UnitPrice = Column(Float)
    Amount = Column(Float)

    invoice = relationship("Invoice", back_populates="items")


# -------------------------
# CREATE
# -------------------------
def create_item(db: Session, item_data: dict) -> Optional[Item]:
    """
    Success:
      - אם invoice קיים -> יוצר Item, עושה commit, refresh ומחזיר Item
    Failure:
      - אם invoice לא קיים -> מחזיר None
    """
    invoice_id = item_data.get("InvoiceId")
    invoice = get_invoice_by_id(db, invoice_id)
    if not invoice:
        return None

    item = Item(
        InvoiceId=invoice_id,
        Description=item_data.get("Description"),
        Name=item_data.get("Name"),
        Quantity=item_data.get("Quantity"),
        UnitPrice=item_data.get("UnitPrice"),
        Amount=item_data.get("Amount"),
    )
    db.add(item)
    db.commit()
    db.refresh
    return item


# -------------------------
# READ
# -------------------------
def get_item_by_id(db: Session, item_id: int) -> Optional[Item]:
    """
    Success: מחזיר Item אם קיים
    Failure: מחזיר None אם לא קיים
    """
    return db.query(Item).filter(Item.id == item_id).first()  # ✅ תיקון: id ולא InvoiceId


def get_items_by_invoice_id(db: Session, invoice_id: str) -> List[Item]:
    """
    מחזיר תמיד list (אולי ריק)
    """
    return db.query(Item).filter(Item.InvoiceId == invoice_id).all()


def get_items(db: Session) -> List[Item]:
    """
    מחזיר תמיד list (אולי ריק)
    """
    return db.query(Item).all()


# -------------------------
# UPDATE
# -------------------------
def update_item(db: Session, item_id: int, update_data: dict) -> Optional[Item]:
    """
    Success:
      - אם item קיים -> מעדכן שדות שמופיעים ב-update_data, עושה commit+refresh ומחזיר Item
    Failure:
      - אם item לא קיים -> מחזיר None
    """
    item = get_item_by_id(db, item_id)
    if not item:
        return None

    # בדרך כלל לא מעדכנים FK InvoiceId, אבל אם רוצים לאפשר - נשאיר.
    if "InvoiceId" in update_data:
        item.InvoiceId = update_data["InvoiceId"]
    if "Description" in update_data:
        item.Description = update_data["Description"]
    if "Name" in update_data:
        item.Name = update_data["Name"]
    if "Quantity" in update_data:
        item.Quantity = update_data["Quantity"]
    if "UnitPrice" in update_data:
        item.UnitPrice = update_data["UnitPrice"]
    if "Amount" in update_data:
        item.Amount = update_data["Amount"]

    db.commit()
    db.refresh(item)
    return item


# -------------------------
# DELETE
# -------------------------
def delete_item(db: Session, item_id: int) -> bool:
    """
    Success: אם item קיים -> מוחק ומחזיר True
    Failure: אם לא קיים -> מחזיר False
    """
    item = get_item_by_id(db, item_id)
    if not item:
        return False

    db.delete(item)
    db.commit()
    return True

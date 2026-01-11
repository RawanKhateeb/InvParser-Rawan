from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from mvc_model.models.base import Base
from mvc_model.db import engine
from mvc_model.db import get_db  
# Controllers
from mvc_model.controller.controller import (
    get_invoice_with_items,
    getInvoiceByVendorNameCon,
    extract_invoice_controller,
    LowConfidenceError,
    ServiceUnavailableError,
)

app = FastAPI()
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

from mvc_model.db import engine
@app.get("/invoice/{invoice_id}")
def getInvoice(invoice_id: str, db: Session = Depends(get_db)):
    result = get_invoice_with_items(db, invoice_id)
    if not result:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return result


@app.get("/invoices/vendor/{vendor_name}")
def getInvoiceByVendorName_view(vendor_name: str, db: Session = Depends(get_db)):
    # כאן אין צורך ב-HTTPException בדרך כלל, כי תמיד מחזירים מבנה תשובה
    return getInvoiceByVendorNameCon(db, vendor_name)


@app.post("/extract")
async def extract(file: UploadFile = File(...), db: Session = Depends(get_db)):
    is_pdf_content_type = file.content_type == "application/pdf"
    is_pdf_filename = bool(file.filename) and file.filename.lower().endswith(".pdf")

    if not (is_pdf_content_type or is_pdf_filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid document. Please upload a valid PDF invoice with high confidence.",
        )

    pdf_bytes = await file.read()

    try:
        result = extract_invoice_controller(db, pdf_bytes)
        return result

    except LowConfidenceError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except ServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unexpected error during extraction.",
        )

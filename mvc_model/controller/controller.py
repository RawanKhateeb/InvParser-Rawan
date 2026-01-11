

import base64
import os
import time
import oci
from mvc_model.models.invoice import create_invoice, get_invoice_by_id, get_invoice_by_vendor_name, get_invoices
from mvc_model.models.item import create_item, get_items_by_invoice_id
from mvc_model.models.confidence import create_confidence
from mvc_model.services.oci_client import get_doc_client

def get_invoice_with_items(db,invoice_id):
    invoice = get_invoice_by_id(db,invoice_id)
    if invoice : 
        items = get_items_by_invoice_id (db,invoice_id)
        invoice_with_items = {
            "invoice" : invoice,
            "items" : items
        } 
        return invoice_with_items
    return None
    
def getInvoiceByVendorNameCon(db,vendor_name):
    myinvoices = []
    invoices = get_invoice_by_vendor_name(db,vendor_name)
    for i in invoices:
        print(i.InvoiceId)

    if invoices : 
        for invoice in invoices:
            invoice_id = invoice.InvoiceId
            items = get_items_by_invoice_id(db,invoice_id)
            invoice_with_items = {
                    "invoice" : invoice,
                    "items" : items
                } 
            myinvoices.append(invoice_with_items)
            
    return {"VendorName": vendor_name if invoices else "Unknown Vendor",
            "TotalInvoices": len(myinvoices),
            "invoices":myinvoices}
   

   
class InvalidPDFError(Exception):
    pass


class ServiceUnavailableError(Exception):
    pass


class LowConfidenceError(Exception):
    pass


def extract_invoice_controller(db, pdf_bytes: bytes) -> dict:
    # 1) Encode PDF to base64
    encoded_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

    # 2) Build OCI request
    document = oci.ai_document.models.InlineDocumentDetails(data=encoded_pdf)
    request = oci.ai_document.models.AnalyzeDocumentDetails(
        document=document,
        features=[
            oci.ai_document.models.DocumentFeature(feature_type="KEY_VALUE_EXTRACTION"),
            oci.ai_document.models.DocumentClassificationFeature(max_results=5),
        ],
    )

    # 3) Call OCI service + measure time
    try:
        start_time = time.time()
        client = get_doc_client()
        response = client.analyze_document(request)
        prediction_time = time.time() - start_time
    except Exception:
        raise ServiceUnavailableError("The service is currently unavailable. Please try again later.")

    # 4) Parse OCI response
    data = {}
    data_confidence = {}
    all_items = []

    for page in response.data.pages:
        if not page.document_fields:
            continue

        for myfield in page.document_fields:
            field_key = myfield.field_label.name if myfield.field_label and myfield.field_label.name else ""
            field_value = myfield.field_value.text if myfield.field_value and myfield.field_value.text else ""

            if field_key == "InvoiceDate":
                field_value = format_date_to_iso(field_value)

            if field_key in ("InvoiceTotal", "SubTotal", "ShippingCost", "Amount", "UnitPrice", "AmountDue"):
                field_value = clean_amount(field_key, field_value)

            field_conf = (
                myfield.field_label.confidence
                if myfield.field_label and myfield.field_label.confidence is not None
                else 0.0
            )

            # Items special handling
            if field_key == "Items":
                all_items = []
                for i in myfield.field_value.items:
                    item = {}
                    for j in i.field_value.items:
                        item_key = j.field_label.name if j.field_label else ""
                        item_value = j.field_value.text if j.field_value and j.field_value.text else ""

                        if item_key in ("Quantity", "UnitPrice", "Amount"):
                            item_value = clean_amount(item_key, item_value)

                        item[item_key] = item_value

                    all_items.append(item)

                field_value = all_items

            data[field_key] = field_value
            data_confidence[field_key] = field_conf

    # 5) Validate doc type confidence threshold
    doc_confidence = 0.0
    if response.data.detected_document_types:
        for validCon in response.data.detected_document_types:
            doc_confidence = validCon.confidence
            if doc_confidence < 0.9:
                raise LowConfidenceError("Invalid document. Please upload a valid PDF invoice with high confidence.")

    # 6) Build result
    result = {
        "confidence": doc_confidence,
        "data": data,
        "dataConfidence": data_confidence,
        "predictionTime": prediction_time,
    }
    # 7) Save to DB using models (CRUD)
    #    - Create invoice
    #created = get_invoice_by_id(db,data.get("InvoiceId"))
    #if not created:
    invoice_obj = create_invoice(db, data)
        #    - Create items (if exist)
    for item_dict in data.get("Items", []):
        item_dict["InvoiceId"] = invoice_obj.InvoiceId
        create_item(db, item_dict)

        #    - Create confidence row
    create_confidence(
        db,
        {
        "InvoiceId": invoice_obj.InvoiceId,
        "VendorName": data_confidence.get("VendorName", 0.0),
        "InvoiceDate": data_confidence.get("InvoiceDate", 0.0),
        "BillingAddressRecipient": data_confidence.get("BillingAddressRecipient", 0.0),
        "ShippingAddress": data_confidence.get("ShippingAddress", 0.0),
        "SubTotal": data_confidence.get("SubTotal", 0.0),
        "ShippingCost": data_confidence.get("ShippingCost", 0.0),
        "InvoiceTotal": data_confidence.get("InvoiceTotal", 0.0),
    },
)
    return result

###################################################Cleaner Functions################################## 
"""
    Converts a date string to ISO 8601 format with UTC timezone.
    Returns empty string if conversion fails.
"""
from datetime import date, datetime, timezone

def format_date_to_iso(date_text):
    if date_text is None:
        return ""

    # If already a datetime/date object
    if isinstance(date_text, datetime):
        dt = date_text
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    if isinstance(date_text, date) and not isinstance(date_text, datetime):
        dt = datetime(date_text.year, date_text.month, date_text.day, tzinfo=timezone.utc)
        return dt.isoformat()

    s = str(date_text).strip()
    if not s:
        return ""

    # Already ISO (with timezone or Z)
    try:
        if "T" in s:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
    except ValueError:
        pass

    # Try multiple common formats
    fmts = [
        "%B %d %Y",   # March 6, 2012
        "%b %d %Y",   # Mar 6, 2012
        "%m/%d/%Y",    # 03/06/2012
        "%m/%d/%y",    # 03/06/12
        "%m-%d-%Y",    # 03-06-2012
        "%Y-%m-%d",    # 2012-03-06
        "%d/%m/%Y",    # 06/03/2012 (if OCR outputs this)
        "%d-%b-%Y",    # 06-Mar-2012
        "%d %b %Y",    # 06 Mar 2012
    ]

    for fmt in fmts:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue

    # If nothing matched, keep old behavior
    return ""

"""
    Removes currency symbols and formatting from amount strings.
    Returns float or empty string if invalid.
"""  
def clean_amount(key,value): 

    if not value:
        return ""
    try:
        if key == "Quantity":
            return int(
            value.replace("$", "").replace(",", "").strip()
        )
        return float(
            value.replace("$", "").replace(",", "").strip()
        )
    except ValueError:
        return ""
import sqlite3
from fastapi import FastAPI, UploadFile, File
import oci
import base64
import json
from fastapi import HTTPException
import db_util 
from datetime import date, datetime, timezone
import time

app = FastAPI()
# Load OCI config from ~/.oci/config
#config = oci.config.from_file()
#doc_client = oci.ai_document.AIServiceDocumentClient(config)

doc_client = None

def get_doc_client():
    global doc_client
    if doc_client is None:
        config = oci.config.from_file()
        doc_client = oci.ai_document.AIServiceDocumentClient(config)
    return doc_client


"""
    Receives an uploaded file and processes it for data extraction.
    This endpoint accepts a file via an HTTP POST request (multipart/form-data).
    The uploaded file is read and handled asynchronously.
    Parameters:
        file (UploadFile): The file uploaded by the client.
    Returns:
        dict: A JSON response containing the extracted data or processing result.
"""
@app.post("/extract")
async def extract(file: UploadFile = File(...)):
  
    # Check if the uploaded file type is PDF
    is_pdf_content_type = file.content_type == "application/pdf"
    # Check if the uploaded file name ends with ".pdf"
    is_pdf_filename = file.filename.lower().endswith(".pdf")
    # Validate that the file is a PDF by content type or file extension
    if not (is_pdf_content_type or is_pdf_filename):
        # Raise an HTTP 400 error if the file is not a valid PDF
        raise HTTPException(
            status_code=400,
            detail="Invalid document. Please upload a valid PDF invoice with high confidence."
        )
    
    #Processes an uploaded PDF by encoding it to Base64 and submitting it to
    #OCI AI Document for key-value extraction and document classification.
    pdf_bytes = await file.read()
    # Base64 encode PDF
    encoded_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    document = oci.ai_document.models.InlineDocumentDetails(
        data=encoded_pdf
    )
    request = oci.ai_document.models.AnalyzeDocumentDetails(
        document=document,
        features=[
            oci.ai_document.models.DocumentFeature(
                feature_type="KEY_VALUE_EXTRACTION"
            ),
            oci.ai_document.models.DocumentClassificationFeature(
                max_results=5
            )
        ]
    )
    try:
        start_time = time.time()   # זמן התחלה
        client = get_doc_client()
        response = client.analyze_document(request)        
        end_time = time.time()     # זמן סיום
        prediction_time = end_time - start_time
        print(f"Time taken: {prediction_time:.2f} seconds")


    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "The service is currently unavailable. Please try again later."
            }
        )
    
    ###############################################START MY CODE######################################################

    data={}  # Stores the final extracted data returned by the OCI service 
    data_Confidence = {} # Stores confidence values associated with the extracted fields
    item = {}        # Represents a single extracted item
    all_items = []   # Stores all extracted items
    #------------------------------------------------------------------
    # Iterate over all pages returned in the OCI document analysis response
    for page in response.data.pages:
        # Check if the page contains extracted document fields
        if page.document_fields:
            # Iterate over each extracted field on the page
            for myfield in page.document_fields:
                # Extract the field name (key) from the field label
                field_key =myfield.field_label.name if myfield.field_label and myfield.field_label.name else ""
                # Extract the field value text, or use an empty string if missing
                field_value = myfield.field_value.text if myfield.field_value and myfield.field_value.text else ""
                if field_key == "InvoiceDate":
                    field_value = format_date_to_iso(field_value)
                if field_key in ("InvoiceTotal", "SubTotal", "ShippingCost", "Amount", "UnitPrice","AmountDue"):
                    field_value = clean_amount(field_key,field_value)
                # Extract the confidence score for the field label,
                # or default to 0.0 if confidence is not available
                field_confidence = myfield.field_label.confidence if myfield.field_label and myfield.field_label.confidence is not None else 0.0
                # Handle the special "Items" field which contains a list of line items
                if field_key == "Items":
                    # Reset the list for this invoice/document (avoid accumulating items across pages)
                    all_items = []
                    # Iterate over each item in the extracted Items field
                    for i in myfield.field_value.items:
                        # Dictionary to store the data of a single item
                        item={}
                        # Iterate over the fields inside the current item
                        for j in i.field_value.items:
                            # Extract the field name (key) if the field label exists
                            item_key = j.field_label.name if j.field_label else ""
                            # Extract the field value text if available, otherwise use an empty string
                            item_value = j.field_value.text if j.field_value and j.field_value.text else ""
                            if item_key in ("Quantity", "UnitPrice", "Amount"):
                                item_value = clean_amount(item_key,item_value)
                            # Store the extracted key-value pair in the current item dictionary
                            item[item_key]=item_value
                        # Append the completed item to the list of all extracted items
                        all_items.append(item)
                    # Assign the extracted list of items as the final value for the current field
                    field_value=all_items
                # Store the extracted field value in the main data dictionary using the field key
                data[field_key]=field_value
                # Store the confidence score associated with this field under the same key
                data_Confidence[field_key]=field_confidence
    # Check if OCI returned detected document types (field is optional)
    confid = 0.0
    if response.data.detected_document_types:
        # Iterate over detected document types
        for validCon in response.data.detected_document_types:
            # Extract the confidence score
            confid = validCon.confidence
            # Reject the document if confidence is below the threshold
            if confid <0.9 :
                raise HTTPException(
                status_code=400,
                detail="Invalid document. Please upload a valid PDF invoice with high confidence."
            )
    # Build the final response object to be returned to the client       
    result = {
        "confidence": confid,
        "data": data,
        "dataConfidence": data_Confidence,
        "predictionTime": prediction_time  # add the prediction time to the response
    }   
    # Save the extracted invoice data and confidence information to the database  
    """try:
        db_util.save_inv_extraction(result)
        except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to save extraction result"
    )"""
    db_util.save_inv_extraction(result)
    # Return the final result as the API response
    return result
"""
    Retrieves an invoice by its unique identifier.
    This endpoint fetches invoice data from the database using the provided
    invoice ID. If the invoice does not exist, a 404 error is returned.
    Parameters:
        invoice_id : The unique identifier of the invoice.
    Returns:
        dict: The invoice data if found.
    Raises:
        HTTPException: 404 error if the invoice is not found.
"""
@app.get("/invoice/{invoice_id}")
def getInvoice(invoice_id):
    # Retrieve the invoice record from the database using the invoice ID
    invoice = db_util.getInvoiceById(invoice_id)
    # If no invoice was found, return a 404 Not Found error
    if not invoice:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found"
        )
    # Return the invoice data as the API response
    return invoice


"""
    Retrieves all invoices associated with a specific vendor.
    This endpoint fetches invoices from the database that match the given
    vendor name. If no invoices are found, the response indicates an
    unknown vendor and returns an empty list.
    Parameters:
        vendor_name (str): The name of the vendor.
    Returns:
        dict: A response containing the vendor name, total number of invoices,
              and a list of matching invoices.
"""
@app.get("/invoices/vendor/{vendor_name}")
def getInvoiceByVendorName(vendor_name):
    # Retrieve all invoices for the given vendor name from the database
    invoices = db_util.get_invoices_by_vendor(vendor_name)
    # Return the response with vendor details and invoice information
    return {"VendorName": vendor_name if invoices else "Unknown Vendor",
            "TotalInvoices": len(invoices),
            "invoices":invoices}

###################################################Cleaner Functions################################## 
"""
    Converts a date string to ISO 8601 format with UTC timezone.
    Returns empty string if conversion fails.
"""
from datetime import datetime, timezone

def format_date_to_iso(date_text): # pragma: no cover
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
def clean_amount(key,value):# pragma: no cover

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

if __name__ == "__main__": # pragma: no cover
    import uvicorn
    db_util.init_db()
    uvicorn.run(app, host="0.0.0.0", port=8080)
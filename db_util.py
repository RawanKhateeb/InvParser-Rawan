import sqlite3     # SQLite database engine (file-based DB)
from contextlib import contextmanager     # Helps create a safe DB connection context manager
import app         # Imported but not used here 

# Path/name of the SQLite database file 
DB_PATH = "invoices.db"

@contextmanager
def get_db():
    """
    Open a database connection and automatically commit/close it.

    Why we use it:
    - Ensures every DB operation uses the same pattern:
      open connection -> do work -> commit -> close
    - Prevents forgetting conn.close() or conn.commit()
    """
    conn = sqlite3.connect(DB_PATH)     # Create a new connection to the DB file
    try:
        yield conn     # Yield the connection to the calling code
        conn.commit()  # Commit changes after successful operations
    finally:
        conn.close()   # Always close connection (even if an error happens)
            
        


def init_db():
    """
    Initialize the DB schema: create tables if they do not exist.

    Tables:
    - invoices: main invoice data (one row per invoice)
    - confidences: confidence score per extracted field (one row per invoice)
    - items: invoice line items (multiple rows per invoice)
    """
    with get_db() as conn:      # Open DB connection using our context manager
        cursor = conn.cursor()   # Cursor executes SQL commands
         # Create 'invoices' table: stores the extracted invoice fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                InvoiceId TEXT PRIMARY KEY,     -- Unique invoice identifier (primary key)
                VendorName TEXT,                -- Vendor / supplier name
                InvoiceDate TEXT,               -- Invoice date (stored as text)
                BillingAddressRecipient TEXT,     -- Person/company receiving the bill  
                ShippingAddress TEXT,           -- Shipping address
                SubTotal REAL,                  -- Subtotal value
                ShippingCost REAL,              -- Shipping cost
                InvoiceTotal REAL                -- Final total
            )
        """)
        # Create 'confidences' table: stores confidence for each extracted field
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS confidences (
                InvoiceId TEXT PRIMARY KEY,      -- Same invoice id, one-to-one with invoices
                VendorName REAL,                 -- Confidence score for VendorName
                InvoiceDate REAL,                -- Confidence score for InvoiceDate
                BillingAddressRecipient REAL,    -- Confidence score for BillingAddressRecipient
                ShippingAddress REAL,            -- Confidence score for ShippingAddress
                SubTotal REAL,                   -- Confidence score for SubTotal
                ShippingCost REAL,                -- Confidence score for ShippingCost
                InvoiceTotal REAL,                 -- Confidence score for InvoiceTotal
                FOREIGN KEY (InvoiceId) REFERENCES invoices(InvoiceId)            -- Ensures this invoice must exist in invoices table
            )
        """)
        # Create 'items' table: stores invoice line items (one invoice can have many items)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,    -- Unique auto ID for each item row
                InvoiceId TEXT,                          -- Which invoice this item belongs to
                Description TEXT,                        -- Item description
                Name TEXT,                               -- Item name
                Quantity REAL,                           -- Quantity (REAL because OCI may output decimals)
                UnitPrice REAL,                          -- Unit price
                Amount REAL,                             -- Total for the line item
                FOREIGN KEY (InvoiceId) REFERENCES invoices(InvoiceId)
                                                      -- Links each item to an invoice
            )
        """)


def save_inv_extraction(result):
    """
    Save the extracted invoice result into the DB.

    result is expected to match:
    {
      "confidence": <document confidence>,
      "data": {...invoice fields...},
      "dataConfidence": {...confidence per field...}
    }
    """
    data = result.get("data", {})                          # Extract the invoice fields dictionary safely
    data_confidence = result.get("dataConfidence", {})     # Extract confidence per field safely
    
    invoice_id = data.get("InvoiceId")                        # InvoiceId is the primary key   
    if invoice_id:       # Only save if InvoiceId exists
        with get_db() as conn:          # Open DB connection
            cursor = conn.cursor()      # Create cursor for SQL
            
            # Insert invoice   # Insert or replace invoice row (replace allows updating same InvoiceId)
            cursor.execute("""
                INSERT OR REPLACE INTO invoices 
                (InvoiceId, VendorName, InvoiceDate, BillingAddressRecipient, 
                 ShippingAddress, SubTotal, ShippingCost, InvoiceTotal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_id,
                data.get("VendorName"),
                data.get("InvoiceDate"),
                data.get("BillingAddressRecipient"),
                data.get("ShippingAddress"),
                data.get("SubTotal"),
                data.get("ShippingCost"),
                data.get("InvoiceTotal")
            ))
            
            # Insert confidences         # Insert or replace confidence row (one row per invoice)
            cursor.execute("""
                INSERT OR REPLACE INTO confidences 
                (InvoiceId, VendorName, InvoiceDate, BillingAddressRecipient,
                 ShippingAddress, SubTotal, ShippingCost, InvoiceTotal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_id,    # Same InvoiceId
                data_confidence.get("VendorName"),  # Confidence for VendorName
                data_confidence.get("InvoiceDate"),   # Confidence for InvoiceDate
                data_confidence.get("BillingAddressRecipient"),
                data_confidence.get("ShippingAddress"),
                data_confidence.get("SubTotal"),
                data_confidence.get("ShippingCost"),
                data_confidence.get("InvoiceTotal")
            ))
            
            # Insert line items
            # First delete existing items for this invoice to avoid duplicates on replace
            line_items = data.get("Items", [])    # List of item dicts
            cursor.execute("DELETE FROM items WHERE InvoiceId = ?", (invoice_id,))
             # Insert each item as its own row in items table
            for item in line_items:
                cursor.execute("""
                    INSERT INTO items 
                    (InvoiceId, Description, Name, Quantity, UnitPrice, Amount)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    invoice_id,  # Foreign key referencing invoice
                    item.get("Description"),
                    item.get("Name"),
                    item.get("Quantity"),
                    item.get("UnitPrice"),
                    item.get("Amount")
                ))

def get_invoices_by_vendor(vendor_name): #Retrieve all invoices for a given vendor name.Returns:A list of full invoice dictionaries (each includes Items)
    
    with get_db() as conn:    # Open DB connection
        cursor = conn.cursor()   # Cursor for SQL
        cursor.execute("select InvoiceId from invoices where VendorName = ?",(vendor_name,))
        rows= cursor.fetchall()              # List of tuples [(InvoiceId,), ...]
        invoices = []                         # Will store full invoice dictionaries
         # For each invoice id found, fetch full invoice details using getInvoiceById()
        for r in rows:
            invoice_id = r[0]                  # Tuple first element = InvoiceId
            invoices.append(getInvoiceById(invoice_id))   # Fetch full invoice structure

    return invoices

def getInvoiceById(invoice_id): #Retrieve a full invoice by its ID (including Items).
    #Returns:
    #- dict with invoice fields and Items list    - None if invoice does not exist
    with get_db() as conn:         # Open DB connection
        cursor = conn.cursor()
        # Select invoice row from invoices table
        cursor.execute("""
            SELECT *
            FROM invoices
            WHERE InvoiceId = ?;
        """, (invoice_id,))
        row = cursor.fetchone()      # Single row or None
        # If invoice doesn't exist, return None
        if not row:
            return None
         # Select all items that belong to this invoice
        cursor.execute("""
            SELECT Description, Name, Quantity, UnitPrice, Amount
            FROM items
            WHERE InvoiceId = ?;
        """, (invoice_id,))
        items_rows = cursor.fetchall()    # List of item rows
      # Convert items rows into list of dictionaries
    items = []
    for item in items_rows:
        items.append({
            "Description": item[0],
            "Name": item[1],
            "Quantity": item[2],
            "UnitPrice": item[3],
            "Amount": item[4]
        })
# Convert invoice row into a dictionary that matches API response scheme
    return {
        "InvoiceId": row[0],
        "VendorName": row[1],
        "InvoiceDate": row[2],
        "BillingAddressRecipient": row[3],
        "ShippingAddress": row[4],
        "SubTotal": row[5],
        "ShippingCost": row[6],
        "InvoiceTotal": row[7],
        "Items": items
    }
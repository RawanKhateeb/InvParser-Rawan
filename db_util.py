import sqlite3
from contextlib import contextmanager



DB_PATH = "invoices.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                InvoiceId TEXT PRIMARY KEY,
                VendorName TEXT,
                InvoiceDate TEXT,
                BillingAddressRecipient TEXT,
                ShippingAddress TEXT,
                SubTotal REAL,
                ShippingCost REAL,
                InvoiceTotal REAL
                
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS confidences (
                InvoiceId TEXT PRIMARY KEY,
                VendorName REAL,
                InvoiceDate REAL,
                BillingAddressRecipient REAL,
                ShippingAddress REAL,
                SubTotal REAL,
                ShippingCost REAL,
                InvoiceTotal REAL,
                FOREIGN KEY (InvoiceId) REFERENCES invoices(InvoiceId)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                InvoiceId TEXT,
                Description TEXT,
                Name TEXT,
                Quantity REAL,
                UnitPrice REAL,
                Amount REAL,
                FOREIGN KEY (InvoiceId) REFERENCES invoices(InvoiceId)
            )
        """)


def save_inv_extraction(result):
    data = result.get("data", {})
    data_confidence = result.get("dataConfidence", {})
    
    invoice_id = data.get("InvoiceId")
    if invoice_id:
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Insert invoice
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
            
            # Insert confidences
            cursor.execute("""
                INSERT OR REPLACE INTO confidences 
                (InvoiceId, VendorName, InvoiceDate, BillingAddressRecipient,
                 ShippingAddress, SubTotal, ShippingCost, InvoiceTotal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_id,
                data_confidence.get("VendorName"),
                data_confidence.get("InvoiceDate"),
                data_confidence.get("BillingAddressRecipient"),
                data_confidence.get("ShippingAddress"),
                data_confidence.get("SubTotal"),
                data_confidence.get("ShippingCost"),
                data_confidence.get("InvoiceTotal")
            ))
            
            # Insert line items
            line_items = data.get("Items", [])
            cursor.execute("DELETE FROM items WHERE InvoiceId = ?", (invoice_id,))
            for item in line_items:
                cursor.execute("""
                    INSERT INTO items 
                    (InvoiceId, Description, Name, Quantity, UnitPrice, Amount)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    invoice_id,
                    item.get("Description"),
                    item.get("Name"),
                    item.get("Quantity"),
                    item.get("UnitPrice"),
                    item.get("Amount")
                ))
"""
    Retrieves all invoices associated with a given vendor name.
    This function queries the database for invoice IDs that match the provided
    vendor name, then fetches the full invoice details for each invoice ID.
    Parameters:
        vendor_name (str): The name of the vendor.
    Returns:
        list: A list of invoice records associated with the vendor.
              Returns an empty list if no invoices are found.
"""
def get_invoices_by_vendor(vendor_name):
    # Open a database connection using the context manager
    with get_db() as conn:
        # Create a database cursor to execute SQL queries
        cursor = conn.cursor()
        # Execute a query to retrieve invoice IDs for the given vendor name
        cursor.execute("select InvoiceId from invoices where VendorName = ?",(vendor_name,))
        # Fetch all matching rows from the query result
        rows= cursor.fetchall()
        invoices = []
        # Iterate over each returned row
        for r in rows:
            invoice_id = r[0]  
            # Retrieve the full invoice details using the invoice ID
            invoices.append(getInvoiceById(invoice_id))  
    # Return the list of invoices associated with the vendor        
    return invoices
"""
    Retrieves a single invoice and its associated items by invoice ID.
    This function queries the database for an invoice record using the given
    invoice ID. If the invoice exists, it also retrieves all related line items
    from the items table and returns a structured dictionary containing the
    invoice details and its items.
    Parameters:
        invoice_id (str | int): The unique identifier of the invoice.
    Returns:
        dict | None: A dictionary containing invoice details and items if found,
                     or None if the invoice does not exist.
"""
def getInvoiceById(invoice_id):
    with get_db() as conn:
        cursor = conn.cursor()
        # Query the invoices table for the invoice with the given ID
        cursor.execute("""
            SELECT *
            FROM invoices
            WHERE InvoiceId = ?;
        """, (invoice_id,))
        # Fetch a single invoice record
        row = cursor.fetchone()
        if not row:
            return None
        # Query the items table for all items related to the invoice
        cursor.execute("""
            SELECT Description, Name, Quantity, UnitPrice, Amount
            FROM items
            WHERE InvoiceId = ?;
        """, (invoice_id,))
        # Fetch all item rows related to the invoice
        items_rows = cursor.fetchall()
    
    items = []
    # Iterate over each item row and build a structured dictionary
    for item in items_rows:
        items.append({
            "Description": item[0],
            "Name": item[1],
            "Quantity": item[2],
            "UnitPrice": item[3],
            "Amount": item[4]
        })
    # Return the full invoice data including its items
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
def clean_db():
    """
    Cleans the database by removing all test data.
    This function is used after each integration test
    to ensure database isolation.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Delete child table first (because of FK relations)
        cursor.execute("DELETE FROM items;")
        cursor.execute("DELETE FROM invoices;")

        conn.commit()


    
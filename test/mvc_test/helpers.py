def get_invoice_data():
     invoice_data  = {
            "VendorName": "SuperStore",
            "InvoiceId": "2910",
            "InvoiceDate": "2012-03-06T00:00:00+00:00",
            "ShippingAddress": "98103, Seattle, Washington, United States",
            "BillingAddressRecipient": "Aaron Bergman",
            "SubTotal": 53.82,
            "ShippingCost": 4.29,
            "InvoiceTotal": 58.11,}
     return invoice_data

def get_update_invoice():
    invoice_data  = {
            "VendorName": "Google",
            "InvoiceId": "2910",
            "InvoiceDate": "2013-03-06T00:00:00+00:00",
            }
    return invoice_data

def get_item_data():
     item_data = {
    "InvoiceId": "2910",
    "Description": "USB-C Charging Cable",
    "Name": "USB Cable",
    "Quantity": 2,
    "UnitPrice": 9.99,
    "Amount": 19.98 }
     
     return item_data

def get_confidence_data():
    return {
        "InvoiceId": "2910",
        "VendorName": 0.99,
        "InvoiceDate": 0.95,
        "BillingAddressRecipient": 0.90,
        "ShippingAddress": 0.92,
        "SubTotal": 0.97,
        "ShippingCost": 0.88,
        "InvoiceTotal": 0.98,
    }

# API Traceability Matrix – InvParser

This document maps each API endpoint to its corresponding integration tests.

| Endpoint | Method | Scenario | Test Case | Test File |
|---------|--------|----------|-----------|-----------|
| /extract | POST | Valid PDF extraction | test_extract_valid_pdf_success | tests/test_extract.py |
| /extract | POST | Reject non-PDF file | test_extract_reject_non_pdf | tests/test_extract.py |
| /invoice/{invoice_id} | GET | Invoice not found | test_get_invoice_not_found | tests/test_invoice_by_id.py |
| /invoice/{invoice_id} | GET | Invoice exists | test_get_invoice_success | tests/test_invoice_by_id.py |
| /invoices/vendor/{vendor_name} | GET | Vendor not found | test_get_invoices_by_vendor_empty | tests/test_invoice_by_vendor.py |
| /invoices/vendor/{vendor_name} | GET | Vendor exists | test_get_invoices_by_vendor_success | tests/test_invoice_by_vendor.py |

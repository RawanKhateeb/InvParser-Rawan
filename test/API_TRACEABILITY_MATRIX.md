# API Traceability Matrix — InvParser Application

This document maps each API endpoint to the automated test cases that validate
its expected behavior and error handling.

## API Coverage

| API Endpoint | Scenario / Behavior | Test File | Test Case |
|--------------|---------------------|----------|-----------|
| *POST /extract* | Successful extraction from a valid PDF and JSON response returned | test/test_extract_new.py | TestYourFeature.test_endpoint_success_case |
| *POST /extract* | Validation failure when document confidence is below threshold | test/test_extract_new.py | TestYourFeature.test_extract_failure_low_confidence |
| *POST /extract* | OCI Document AI service unavailable → returns 503 | test/test_extract_new.py | TestYourFeature.test_extract_failure_oci_down |
| *POST /extract* | Database save failure handled by API → returns 503 | test/test_extract_new.py | TestYourFeature.test_extract_failure_db_save |
| *POST /extract* | Edge case: extraction returns empty fields → 200 with empty payload | test/test_extract_new.py | TestYourFeature.test_extract_empty_document_fields_returns_empty_data |
| *GET /invoice/{invoice_id}* | Invoice exists → invoice data returned | test/test_get_invoice_by_id.py | TestGetInvoiceById.test_invoice_found |
| *GET /invoice/{invoice_id}* | Invoice not found → returns 404 | test/test_get_invoice_by_id.py | TestGetInvoiceById.test_invoice_not_found |
| *GET /invoices/vendor/{vendor_name}* | Vendor exists → list of invoices returned | test/test_get_invoices_by_vendor_name.py | TestGetInvoicesByVendorName.test_invoice_by_vendor_found |
| *GET /invoices/vendor/{vendor_name}* | Vendor has no invoices → empty list or “Unknown Vendor” response | test/test_get_invoices_by_vendor_name.py | TestGetInvoicesByVendorName.test_invoice_not_found_vendor |

## Notes
- All tests are implemented as *integration tests* using FastAPI’s TestClient
  and a real SQLite database.
- The OCI Document AI service is *mocked* in /extract tests to remove external
  dependencies and enable execution in CI environments without OCI credentials
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

# עדכני את ה-import הזה לפי הנתיב האמיתי של קובץ ה-View שלך
from mvc_model.myAppView import app, get_db


class TestViewEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

        # Dummy DB session (we don't want real DB in VIEW tests)
        self.db_mock = MagicMock()

        # Override FastAPI dependency
        def override_get_db():
            yield self.db_mock

        app.dependency_overrides[get_db] = override_get_db

    def tearDown(self):
        app.dependency_overrides.clear()

    # -------------------- /invoice/{invoice_id} --------------------

    @patch("mvc_model.myAppView.get_invoice_with_items")
    def test_get_invoice_success(self, mock_controller):
        mock_controller.return_value = {
            "invoice": {"InvoiceId": "2910", "VendorName": "SuperStore"},
            "items": [{"id": 1, "InvoiceId": "2910"}],
        }

        resp = self.client.get("/invoice/2910")
        self.assertEqual(resp.status_code, 200)

        body = resp.json()
        self.assertIn("invoice", body)
        self.assertIn("items", body)
        self.assertEqual(body["invoice"]["InvoiceId"], "2910")

    @patch("mvc_model.myAppView.get_invoice_with_items")
    def test_get_invoice_not_found(self, mock_controller):
        mock_controller.return_value = None  # controller returns None => 404 in view

        resp = self.client.get("/invoice/NOT_EXISTS")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.json()["detail"], "Invoice not found")

    # -------------------- /invoices/vendor/{vendor_name} --------------------

    @patch("mvc_model.myAppView.getInvoiceByVendorNameCon")
    def test_get_invoices_by_vendor_success(self, mock_controller):
        mock_controller.return_value = {
            "VendorName": "SuperStore",
            "TotalInvoices": 1,
            "invoices": [
                {"invoice": {"InvoiceId": "2910"}, "items": [{"id": 1}]}
            ],
        }

        resp = self.client.get("/invoices/vendor/SuperStore")
        self.assertEqual(resp.status_code, 200)

        body = resp.json()
        self.assertEqual(body["VendorName"], "SuperStore")
        self.assertEqual(body["TotalInvoices"], 1)
        self.assertIsInstance(body["invoices"], list)

    @patch("mvc_model.myAppView.getInvoiceByVendorNameCon")
    def test_get_invoices_by_vendor_empty(self, mock_controller):
        mock_controller.return_value = {"VendorName": "Unknown Vendor", "TotalInvoices": 0, "invoices": []}

        resp = self.client.get("/invoices/vendor/NO_VENDOR")
        self.assertEqual(resp.status_code, 200)

        body = resp.json()
        self.assertEqual(body["VendorName"], "Unknown Vendor")
        self.assertEqual(body["TotalInvoices"], 0)
        self.assertEqual(body["invoices"], [])

    # -------------------- /extract --------------------

    def test_extract_invalid_pdf(self):
        # Not a PDF content-type + not .pdf filename => 400
        files = {"file": ("test.txt", b"hello", "text/plain")}
        resp = self.client.post("/extract", files=files)

        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid document", resp.json()["detail"])

    @patch("mvc_model.myAppView.extract_invoice_controller")
    def test_extract_success(self, mock_controller):
        mock_controller.return_value = {
            "confidence": 0.95,
            "data": {"InvoiceId": "2910", "VendorName": "SuperStore", "Items": []},
            "dataConfidence": {"InvoiceId": 0.98},
            "predictionTime": 0.12,
        }

        files = {"file": ("test.pdf", b"%PDF-1.4 fake", "application/pdf")}
        resp = self.client.post("/extract", files=files)

        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("confidence", body)
        self.assertIn("data", body)
        self.assertEqual(body["data"]["InvoiceId"], "2910")

    @patch("mvc_model.myAppView.extract_invoice_controller")
    def test_extract_low_confidence(self, mock_controller):
        # Controller raises LowConfidenceError => view turns it into 400
        from mvc_model.controller.controller import LowConfidenceError
        mock_controller.side_effect = LowConfidenceError("Low confidence")

        files = {"file": ("test.pdf", b"%PDF-1.4 fake", "application/pdf")}
        resp = self.client.post("/extract", files=files)

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["detail"], "Low confidence")

    @patch("mvc_model.myAppView.extract_invoice_controller")
    def test_extract_service_unavailable(self, mock_controller):
        # Controller raises ServiceUnavailableError => view turns it into 503
        from mvc_model.controller.controller import ServiceUnavailableError
        mock_controller.side_effect = ServiceUnavailableError("OCI down")

        files = {"file": ("test.pdf", b"%PDF-1.4 fake", "application/pdf")}
        resp = self.client.post("/extract", files=files)

        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.json()["detail"], "OCI down")

    @patch("mvc_model.myAppView.extract_invoice_controller")
    def test_extract_unexpected_error(self, mock_controller):
        # Any other exception => 500
        mock_controller.side_effect = Exception("boom")

        files = {"file": ("test.pdf", b"%PDF-1.4 fake", "application/pdf")}
        resp = self.client.post("/extract", files=files)

        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.json()["detail"], "Unexpected error during extraction.")


if __name__ == "__main__":
    unittest.main()

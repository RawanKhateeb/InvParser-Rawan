import unittest
from unittest.mock import patch, MagicMock
from db_util import init_db, clean_db
from fastapi.testclient import TestClient
from app import app

"""
Builds a fake OCI response object that matches EXACTLY what extract() code reads:
  - response.data.pages
  - page.document_fields
  - myfield.field_label.name / .confidence
  - myfield.field_value.text
  - Items special structure:
      myfield.field_value.items -> [i, ...]
      i.field_value.items -> [j, ...]
      j.field_label.name / j.field_value.text
  - response.data.detected_document_types -> [obj.confidence]
"""

def build_fake_oci_response(doc_type_confidence=0.95, include_document_fields=True):
    # ---------- helpers ----------
    def make_field(key, value, confidence=0.95):        #1
        f = MagicMock()
        f.field_label.name = key
        f.field_label.confidence = confidence
        f.field_value.text = value
        f.field_value.items = []  # keep safe even for non-Items fields
        return f
    def make_j(item_key, item_value):                   #2
        j = MagicMock()
        j.field_label.name = item_key
        j.field_value.text = item_value
        return j
    def make_i(j_list):                                #3
        i = MagicMock()
        i.field_value.items = j_list
        return i
    def make_items_field(i_list, confidence=0.95):     #4
        items_f = MagicMock()
        items_f.field_label.name = "Items"
        items_f.field_label.confidence = confidence
        items_f.field_value.text = ""         # not used for Items
        items_f.field_value.items = i_list    # IMPORTANT
        return items_f
    # ---------- build 1 item (i) with inner fields (j) ---------- # bulid a actual item
    j_list = [
        make_j("Description", "Newell 330 Art, Office Supplies, OFF-AR-5309"),
        make_j("Name", "Blue Pen"),
        make_j("Quantity", "2"),
        make_j("UnitPrice", "5.0"),
        make_j("Amount", "10.0"),
    ]
    i1 = make_i(j_list) #One invoice line with internal fields
    # ---------- build document_fields for 1 page ----------
    if include_document_fields:
        document_fields = [
            make_field("InvoiceId", "2910", 0.98),  # note: text values often come as strings
            make_field("VendorName", "SuperStore", 0.97),
            make_field("InvoiceDate", "2012-03-06T00:00:00+00:00", 0.96),
            make_field("SubTotal", "100.0", 0.95),
            make_field("ShippingCost", "10.0", 0.95),
            make_field("InvoiceTotal", "110.0", 0.95),
            make_items_field([i1], confidence=0.95),
        ]
    else:
        document_fields = []
    # ---------- page ----------
    page = MagicMock()
    page.document_fields = document_fields
    # ---------- detected_document_types  ----------
    doc_type = MagicMock()
    doc_type.confidence = doc_type_confidence
    # ---------- response.data ----------
    data = MagicMock()
    data.pages = [page]
    data.detected_document_types = [doc_type]
    # ---------- fake response ----------
    fake_response = MagicMock()
    fake_response.data = data
    return fake_response
#-----------Testing Department-------------------------------------------
class TestYourFeature(unittest.TestCase):
    """Integration tests for POST /extract (success + failures)"""
    def setUp(self):
        init_db()            #Preparing the tests
        self.client = TestClient(app)
        # Fake PDF used in all tests
        self.pdf_bytes = b"%PDF-1.4\n%Fake PDF content\n"
        self.files = {"file": ("test.pdf", self.pdf_bytes, "application/pdf")}
    def tearDown(self):
        clean_db()
    # -------------------- SUCCESS --------------------
    @patch("app.get_doc_client")
    def test_endpoint_success_case(self, mock_get_client):
        fake_response = build_fake_oci_response(doc_type_confidence=0.95, include_document_fields=True)
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.analyze_document.return_value = fake_response
        response = self.client.post("/extract", files=self.files)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIsInstance(result, dict)
        self.assertIn("data", result)
        self.assertIn("confidence", result)
        data = result["data"]
        self.assertEqual(data["InvoiceId"], "2910")
        self.assertEqual(data["VendorName"], "SuperStore")
        self.assertIn("Items", data)
        self.assertIsInstance(data["Items"], list)
        self.assertGreater(len(data["Items"]), 0)
    # -------------------- FAILURE: low confidence -> 400 --------------------
    @patch("app.doc_client")
    def test_extract_failure_low_confidence(self, mock_doc_client):
        fake_response = build_fake_oci_response(doc_type_confidence=0.5, include_document_fields=True)
        mock_doc_client.analyze_document.return_value = fake_response
        response = self.client.post("/extract", files=self.files)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"detail": "Invalid document. Please upload a valid PDF invoice with high confidence."}
        )
    # -------------------- FAILURE: OCI down -> 503 --------------------
    @patch("app.doc_client")
    def test_extract_failure_oci_down(self, mock_doc_client):
        mock_doc_client.analyze_document.side_effect = Exception("OCI down")
        response = self.client.post("/extract", files=self.files)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": {"error": "The service is currently unavailable. Please try again later."}}
        )
    # -------------------- FAILURE: not pdf format -> 400 --------------------
    def test_extract_invalid_file_type_returns_400(self):
        # Not a PDF: wrong content-type and wrong extension
        bad_bytes = b"not a pdf"
        files = {"file": ("test.txt", bad_bytes, "text/plain")}
        response = self.client.post("/extract", files=files)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {"detail": "Invalid document. Please upload a valid PDF invoice with high confidence."}
    )
    # -------------------- FAILURE: DB save fails -> 503 --------------------
    """
    @patch("app.db_util.save_inv_extraction")
    @patch("app.doc_client")
    def test_extract_failure_db_save(self, mock_doc_client, mock_save):
        fake_response = build_fake_oci_response(doc_type_confidence=0.95, include_document_fields=True)
        mock_doc_client.analyze_document.return_value = fake_response
        mock_save.side_effect = Exception("DB error")
        response = self.client.post("/extract", files=self.files)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": {"error": "The service is currently unavailable. Please try again later."}}
        )
        """
    # -------------------- EDGE CASE: empty fields -> 200 with empty data --------------------
    @patch("app.doc_client")
    def test_extract_empty_document_fields_returns_empty_data(self, mock_doc_client):
        fake_response = build_fake_oci_response(doc_type_confidence=0.95, include_document_fields=False)
        mock_doc_client.analyze_document.return_value = fake_response
        response = self.client.post("/extract", files=self.files)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("data", body)
        self.assertEqual(body["data"], {})
        self.assertIn("dataConfidence", body)
        self.assertEqual(body["dataConfidence"], {})

if __name__ == "__main__":
    unittest.main()
import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ✅ IMPORTANT: import the controller from the module where it is defined
from mvc_model.controller.controller import (
    extract_invoice_controller,
    ServiceUnavailableError,
    LowConfidenceError,
)

# ✅ IMPORTANT: import Base and ALSO import models so SQLAlchemy registers tables
from mvc_model.models.base import Base
from mvc_model.models.invoice import get_invoice_by_id
from mvc_model.models.item import get_items_by_invoice_id
from mvc_model.models.confidence import get_confidence_by_invoice_id


def build_fake_oci_response(doc_type_confidence=0.95, include_document_fields=True):
    """
    Builds a fake OCI response object with the attributes your controller reads:
      response.data.pages[*].document_fields[*].field_label.name/confidence
      response.data.pages[*].document_fields[*].field_value.text/items
      response.data.detected_document_types[*].confidence
    """

    def make_field(key, value, confidence=0.95):
        f = MagicMock()
        f.field_label = MagicMock()
        f.field_label.name = key
        f.field_label.confidence = confidence

        f.field_value = MagicMock()
        f.field_value.text = value
        f.field_value.items = []  # safe default
        return f

    def make_j(item_key, item_value):
        j = MagicMock()
        j.field_label = MagicMock()
        j.field_label.name = item_key

        j.field_value = MagicMock()
        j.field_value.text = item_value
        return j

    def make_i(j_list):
        i = MagicMock()
        i.field_value = MagicMock()
        i.field_value.items = j_list
        return i

    def make_items_field(i_list, confidence=0.95):
        items_f = MagicMock()
        items_f.field_label = MagicMock()
        items_f.field_label.name = "Items"
        items_f.field_label.confidence = confidence

        items_f.field_value = MagicMock()
        items_f.field_value.text = ""       # not used for Items
        items_f.field_value.items = i_list  # IMPORTANT
        return items_f

    # Build one line item (i) with inner fields (j)
    j_list = [
        make_j("Description", "USB-C Charging Cable"),
        make_j("Name", "USB Cable"),
        make_j("Quantity", "2"),
        make_j("UnitPrice", "9.99"),
        make_j("Amount", "19.98"),
    ]
    i1 = make_i(j_list)

    # Build document_fields for 1 page
    if include_document_fields:
        document_fields = [
            make_field("InvoiceId", "2910", 0.98),
            make_field("VendorName", "SuperStore", 0.97),
            make_field("InvoiceDate", "2012-03-06T00:00:00+00:00", 0.96),
            make_field("SubTotal", "53.82", 0.95),
            make_field("ShippingCost", "4.29", 0.95),
            make_field("InvoiceTotal", "58.11", 0.95),
            make_items_field([i1], confidence=0.95),
        ]
    else:
        document_fields = []

    page = MagicMock()
    page.document_fields = document_fields

    doc_type = MagicMock()
    doc_type.confidence = doc_type_confidence

    data = MagicMock()
    data.pages = [page]
    data.detected_document_types = [doc_type]

    fake_response = MagicMock()
    fake_response.data = data
    return fake_response


class TestExtractInvoiceController(unittest.TestCase):
    def setUp(self):
        # ✅ In-memory SQLite that persists for the life of the test via StaticPool
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)

        SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.db = SessionLocal()

        # Fake PDF bytes
        self.pdf_bytes = b"%PDF-1.4\n%Fake PDF content\n"

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    # -------------------- SUCCESS --------------------
    @patch("mvc_model.controller.controller.get_doc_client")
    def test_extract_invoice_controller_success(self, mock_get_doc_client):
        # Arrange: mock OCI client + response
        fake_response = build_fake_oci_response(doc_type_confidence=0.95, include_document_fields=True)

        mock_client = MagicMock()
        mock_client.analyze_document.return_value = fake_response
        mock_get_doc_client.return_value = mock_client

        # Act
        result = extract_invoice_controller(self.db, self.pdf_bytes)

        # Assert (response structure)
        self.assertIsInstance(result, dict)
        self.assertIn("confidence", result)
        self.assertIn("data", result)
        self.assertIn("dataConfidence", result)
        self.assertIn("predictionTime", result)

        data = result["data"]
        self.assertEqual(data["InvoiceId"], "2910")
        self.assertEqual(data["VendorName"], "SuperStore")
        self.assertIn("Items", data)
        self.assertIsInstance(data["Items"], list)
        self.assertGreater(len(data["Items"]), 0)

        # Assert (DB persistence): invoice saved
        inv = get_invoice_by_id(self.db, "2910")
        self.assertIsNotNone(inv)
        self.assertEqual(inv.VendorName, "SuperStore")

        # Assert (DB persistence): items saved
        items = get_items_by_invoice_id(self.db, "2910")
        self.assertIsInstance(items, list)
        self.assertGreaterEqual(len(items), 1)
        self.assertEqual(items[0].InvoiceId, "2910")

        # Assert (DB persistence): confidence row saved
        conf = get_confidence_by_invoice_id(self.db, "2910")
        self.assertIsNotNone(conf)
        self.assertEqual(conf.InvoiceId, "2910")

    # -------------------- FAILURE: OCI unavailable --------------------
    @patch("mvc_model.controller.controller.get_doc_client")
    def test_extract_invoice_controller_failure_service_unavailable(self, mock_get_doc_client):
        # Arrange: OCI client raises exception
        mock_client = MagicMock()
        mock_client.analyze_document.side_effect = Exception("OCI down")
        mock_get_doc_client.return_value = mock_client

        # Act + Assert
        with self.assertRaises(ServiceUnavailableError):
            extract_invoice_controller(self.db, self.pdf_bytes)

        # Optional: verify nothing saved
        self.assertIsNone(get_invoice_by_id(self.db, "2910"))

    # -------------------- FAILURE: Low confidence document type --------------------
    @patch("mvc_model.controller.controller.get_doc_client")
    def test_extract_invoice_controller_failure_low_confidence(self, mock_get_doc_client):
        # Arrange: confidence below threshold 0.9
        fake_response = build_fake_oci_response(doc_type_confidence=0.50, include_document_fields=True)

        mock_client = MagicMock()
        mock_client.analyze_document.return_value = fake_response
        mock_get_doc_client.return_value = mock_client

        # Act + Assert
        with self.assertRaises(LowConfidenceError):
            extract_invoice_controller(self.db, self.pdf_bytes)

        # Optional: verify nothing saved
        self.assertIsNone(get_invoice_by_id(self.db, "2910"))


if __name__ == "__main__":
    unittest.main()

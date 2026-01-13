from mvc_model.controller.controller import getInvoiceByVendorNameCon
from test.mvc_test.helpers import get_invoice_data, get_item_data
import unittest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from mvc_model.models.base import Base
from mvc_model.models.invoice import create_invoice
from mvc_model.models.item import create_item
from test.mvc_test.helpers import get_invoice_data, get_item_data


class TestControllerInvoiceByVendorName(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False} 
        )
        Base.metadata.create_all(bind=self.engine)
        SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.db= SessionLocal()

    
    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()
    
    #----------------------------------CONTROLLER-INVOICE-BY-VENDOR-NAME-SUCCESS------------------------#

    def test_get_invoice_by_vendor_name_success(self):
        # Arrange: create invoice + item
        invoice_data = get_invoice_data()
        vendor_name = invoice_data["VendorName"]

        created_invoice = create_invoice(self.db, invoice_data)
        self.assertIsNotNone(created_invoice)

        item_data = get_item_data()
        create_item(self.db, item_data)

        # Act
        result = getInvoiceByVendorNameCon(self.db, vendor_name)

        # Assert – structure
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

        self.assertIn("VendorName", result)
        self.assertIn("TotalInvoices", result)
        self.assertIn("invoices", result)

        # Assert – values
        self.assertEqual(result["VendorName"], vendor_name)
        self.assertGreater(result["TotalInvoices"], 0)
        self.assertIsInstance(result["invoices"], list)

        # Assert – inner structure
        first_entry = result["invoices"][0]
        self.assertIn("invoice", first_entry)
        self.assertIn("items", first_entry)

        self.assertEqual(first_entry["invoice"].VendorName, vendor_name)
        self.assertIsInstance(first_entry["items"], list)

    #----------------------------------CONTROLLER-INVOICE-BY-VENDOR-NAME-FAILUER------------------------#
    def test_get_invoice_by_vendor_name_failure(self):
        # Arrange
        invalid_vendor = "VENDOR_NOT_EXISTS"

        # Act
        result = getInvoiceByVendorNameCon(self.db, invalid_vendor)

        # Assert
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)

        self.assertEqual(result["VendorName"], "Unknown Vendor")
        self.assertEqual(result["TotalInvoices"], 0)
        self.assertIsInstance(result["invoices"], list)
        self.assertEqual(len(result["invoices"]), 0)


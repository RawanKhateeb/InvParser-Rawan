import unittest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from mvc_model.controller.controller import get_invoice_with_items
from mvc_model.models.base import Base
from mvc_model.models.invoice import create_invoice, get_invoice_by_id
from mvc_model.models.item import create_item, get_items_by_invoice_id
from test.mvc_test.helpers import get_invoice_data, get_item_data


class TestControllerInvoiceWithItems(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False} 
        )
        Base.metadata.create_all(bind=self.engine)
        SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.db= SessionLocal()

        self.invoice = get_invoice_data()
        item = get_item_data()

        create_invoice(self.db,self.invoice)
        create_item(self.db,item)
    
    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()
    
    #----------------------------------CONTROLLER-INVOICE-WITH-ITEMS-SUCCESS------------------------#
    def test_get_invoice_with_items_success(self):
        invoice_id = self.invoice["InvoiceId"]
        invoice = get_invoice_by_id(self.db, invoice_id)
        self.assertIsNotNone(invoice)

        items = get_items_by_invoice_id(self.db, invoice_id)
        self.assertIsNotNone(items)

        invoice_with_items = get_invoice_with_items(self.db, invoice_id)
        self.assertIsNotNone(invoice_with_items)

        data = invoice_with_items  # dict

        self.assertIn("invoice", data)
        self.assertIn("items", data)

        self.assertIsNotNone(data["invoice"])
        self.assertIsInstance(data["items"], list)
        self.assertGreaterEqual(len(data["items"]), 1)
    #----------------------------------CONTROLLER-INVOICE-WITH-ITEMS-FAILUER------------------------#

    def test_get_invoice_with_items_failure(self):
        # use invoice_id that does NOT exist in DB
        invalid_invoice_id = "NOT_EXISTS_123"
        invoice_with_items = get_invoice_with_items(self.db, invalid_invoice_id)
        self.assertIsNone(invoice_with_items)





import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from mvc_model.models.base import Base
from mvc_model.models.invoice import Invoice, create_invoice
from mvc_model.models.item import Item, create_item, delete_item, get_item_by_id, update_item
from test.mvc_test.helpers import get_invoice_data, get_item_data


class TestItemCRUD(unittest.TestCase):
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
    #-------------------------------------CRUD-ITEM-SUCCESS------------------------------------#
    def test_create_item_success(self):
        #create invoice
        invoice_data = get_invoice_data()
        invoice = create_invoice(self.db,invoice_data)
        self.assertIsNotNone(invoice)
        self.assertIsInstance(invoice,Invoice)
        self.assertEqual(invoice.InvoiceId,"2910")

        #create item
        item_data = get_item_data()
        created = create_item(self.db,item_data)
        self.assertIsNotNone(created)
        self.assertIsInstance(created,Item)
        self.assertEqual(invoice.InvoiceId,created.InvoiceId)

    def test_get_item_by_id_success(self):
        create_invoice(self.db, get_invoice_data())
        created_item = create_item(self.db, get_item_data())

        item = get_item_by_id(self.db, created_item.id)
        self.assertIsNotNone(item)
        self.assertEqual(item.id, created_item.id)

    def test_update_item_success(self):
        create_invoice(self.db, get_invoice_data())
        created_item = create_item(self.db, get_item_data())

        update_data = {"Name": "New Name", "Quantity": 3}
        updated = update_item(self.db, created_item.id, update_data)

        self.assertIsNotNone(updated)
        self.assertEqual(updated.Name, "New Name")
        self.assertEqual(updated.Quantity, 3)

    def test_delete_item_success(self):
        create_invoice(self.db, get_invoice_data())
        created_item = create_item(self.db, get_item_data())

        ok = delete_item(self.db, created_item.id)
        self.assertTrue(ok)

        after = get_item_by_id(self.db, created_item.id)
        self.assertIsNone(after)

    #-------------------------------------CRUD-ITEM-fAILUER------------------------------------#
    def test_create_item_failure_invoice_not_found(self):
        item_data = get_item_data()
        item_data["InvoiceId"] = "NOT_EXISTS"

        created_item = create_item(self.db, item_data)
        self.assertIsNone(created_item)

    def test_get_item_by_id_failure(self):
        item = get_item_by_id(self.db, 999999)
        self.assertIsNone(item)

    def test_update_item_failure(self):
        update_data = {"Name": "X"}
        updated = update_item(self.db, 999999, update_data)
        self.assertIsNone(updated)

    def test_delete_item_failure(self):
        ok = delete_item(self.db, 999999)
        self.assertFalse(ok)




        
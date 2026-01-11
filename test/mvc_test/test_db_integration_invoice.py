from typing import List, Optional
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mvc_model.models.base import Base          # איפה ש-Base שלך נמצא
# import models כדי ש-SQLAlchemy "יכיר" את הטבלאות
from mvc_model.models.invoice import Invoice, create_invoice, delete_invoice, get_invoice_by_id, get_invoice_by_vendor_name, get_invoices, update_invoice
from test.mvc_test.helpers import get_invoice_data, get_update_invoice


class TestInvoiceCRUD(unittest.TestCase):

    def setUp(self):
        # create SQLITE in memory
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False}
        )
        # create all tables
        Base.metadata.create_all(bind=self.engine)
        # create SessionLocal
        SessionLocal = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False
        )
        # open real  Session 
        self.db = SessionLocal()

    def tearDown(self):
        # close session
        self.db.close()
        # drop all tables
        Base.metadata.drop_all(bind=self.engine)
        # close engine
        self.engine.dispose()
    #-------------------------------------CRUD-INVOICE-SUCCESS------------------------------------#
    def test_create_invoice_success(self):
        invoice_data = get_invoice_data()
        invoice = create_invoice(self.db,invoice_data)
        self.assertIsNotNone(invoice)
        self.assertIsInstance(invoice,Invoice)
        self.assertEqual(invoice.InvoiceId,"2910")
        self.assertEqual(invoice.VendorName,"SuperStore")
    
    def test_get_invoice_by_id_success(self):
        invoice_data = get_invoice_data()#get the invoice data
        invoice_id = invoice_data["InvoiceId"]#extract the id num into variable
        invoice=create_invoice(self.db,invoice_data)#create invoice
        self.assertIsNotNone(invoice)#test if invoice into the variable
        self.assertIsInstance(invoice,Invoice) # the return type is Invoice Object
        invoice_by_id=get_invoice_by_id(self.db,invoice_id)#return invoice by using the model function
        self.assertIsNotNone(invoice_by_id)#check that it is not none
        self.assertEqual(invoice_by_id.InvoiceId, invoice_id)#check that is it the true id

    def test_get_invoice_by_vendor_name_success(self):
        invoice_data = get_invoice_data()  # get the invoice data
        vendor_name = invoice_data["VendorName"]  # extract the vendor name into variable
        invoice = create_invoice(self.db, invoice_data)  # create invoice
        self.assertIsNotNone(invoice)  # test if invoice into the variable
        self.assertIsInstance(invoice, Invoice)  # the return type is Invoice Object
        invoices_by_vendor = get_invoice_by_vendor_name(self.db, vendor_name)
        # runtime type checks (List[Invoice] is only a type-hint, not a runtime type)
        self.assertIsInstance(invoices_by_vendor, list)
        self.assertGreater(len(invoices_by_vendor), 0)
        for inv in invoices_by_vendor:
            self.assertIsInstance(inv, Invoice)
            self.assertEqual(inv.VendorName, vendor_name)
    
    def test_update_invoice_success(self):
        # create initial invoice
        invoice_data = get_invoice_data()
        created = create_invoice(self.db, invoice_data)
        self.assertIsNotNone(created)
        self.assertIsInstance(created, Invoice)
        # prepare update payload
        update_data = get_update_invoice()
        invoice_id = update_data["InvoiceId"]
        # make sure we're updating the same invoice we created
        self.assertEqual(created.InvoiceId, invoice_id)
        # call update with the correct signature: (db, invoice_id, update_data)
        updated = update_invoice(self.db, invoice_id, update_data)
        self.assertIsNotNone(updated)
        self.assertIsInstance(updated, Invoice)
        # verify updated fields
        self.assertEqual(updated.VendorName, update_data["VendorName"])
        self.assertEqual(updated.InvoiceDate, update_data["InvoiceDate"])
        # optional: verify a field that should NOT change (because not in update_data)
        self.assertEqual(updated.InvoiceTotal, invoice_data["InvoiceTotal"])

    def test_get_invoices_success(self):
        # DB should start empty
        invoices_before = get_invoices(self.db)
        self.assertIsInstance(invoices_before, list)
        self.assertEqual(len(invoices_before), 0)
        # create one invoice
        invoice_data = get_invoice_data()
        created = create_invoice(self.db, invoice_data)
        self.assertIsNotNone(created)
        self.assertIsInstance(created, Invoice)
        # now fetch all invoices
        invoices_after = get_invoices(self.db)
        self.assertIsInstance(invoices_after, list)
        self.assertEqual(len(invoices_after), 1)
        self.assertIsInstance(invoices_after[0], Invoice)
        self.assertEqual(invoices_after[0].InvoiceId, invoice_data["InvoiceId"])

    def test_delete_invoice_success(self):
        # create invoice first
        invoice_data = get_invoice_data()
        created = create_invoice(self.db, invoice_data)
        self.assertIsNotNone(created)
        self.assertIsInstance(created, Invoice)
        invoice_id = invoice_data["InvoiceId"]
        # delete it
        deleted = delete_invoice(self.db, invoice_id)
        self.assertTrue(deleted)
        # verify it's gone
        invoice_after = get_invoice_by_id(self.db, invoice_id)
        self.assertIsNone(invoice_after)
        # verify list is empty again
        invoices_after = get_invoices(self.db)
        self.assertEqual(len(invoices_after), 0)
    #-------------------------------------CRUD-INVOICE-FAILUER------------------------------------#
    def test_create_invoice_failuer(self):
        invoice_data = {}
        invoice = create_invoice(self.db,invoice_data)
        self.assertIsNone(invoice)

    def test_get_invoice_by_id_failuer(self):
        invoice_data = get_invoice_data()#get the invoice data
        invoice_id = "9999999"
        invoice=create_invoice(self.db,invoice_data)#create invoice
        invoice_by_id=get_invoice_by_id(self.db,invoice_id)#return invoice by using the model function
        self.assertIsNone(invoice_by_id)#check that it is none

    def test_get_invoice_by_vendor_name_failuer(self):
        invoice_data = get_invoice_data()  # get the invoice data
        vendor_name = "Super" 
        invoice = create_invoice(self.db, invoice_data)  # create invoice
        self.assertIsNotNone(invoice)  # test if invoice into the variable
        self.assertIsInstance(invoice, Invoice)  # the return type is Invoice Object
        invoices_by_vendor = get_invoice_by_vendor_name(self.db, vendor_name)
        self.assertIsInstance(invoices_by_vendor, list)
        self.assertEqual(len(invoices_by_vendor), 0)
       
    def test_update_invoice_failuer(self):
        # create initial invoice
        invoice_data = get_invoice_data()
        created = create_invoice(self.db, invoice_data)
        self.assertIsNotNone(created)
        self.assertIsInstance(created, Invoice)
        # prepare update payload
        update_data = get_update_invoice()
        # try to update non-existing invoice id
        updated = update_invoice(self.db, "999999", update_data)
        self.assertIsNone(updated)
        # verify the original invoice in DB was NOT changed
        invoice_after = get_invoice_by_id(self.db, invoice_data["InvoiceId"])
        self.assertIsNotNone(invoice_after)
        self.assertEqual(invoice_after.VendorName, invoice_data["VendorName"])
        self.assertEqual(invoice_after.InvoiceDate, invoice_data["InvoiceDate"])
        self.assertEqual(invoice_after.InvoiceTotal, invoice_data["InvoiceTotal"])

    def test_delete_invoice_failure(self):
        # create invoice first
        invoice_data = get_invoice_data()
        created = create_invoice(self.db, invoice_data)
        self.assertIsNotNone(created)
        self.assertIsInstance(created, Invoice)
        invoice_id = invoice_data["InvoiceId"]
        # try to delete it
        deleted = delete_invoice(self.db, "99999")
        self.assertFalse(deleted)
        # verify it's not gone
        invoice_after = get_invoice_by_id(self.db, invoice_id)
        self.assertIsNotNone(invoice_after)
        # verify list is not empty 
        invoices_after = get_invoices(self.db)
        self.assertEqual(len(invoices_after),1)
                

        





       


        


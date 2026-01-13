import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import unittest
from mvc_model.models.base import Base
from mvc_model.models.confidence import Confidence, create_confidence, delete_confidence, get_confidence_by_invoice_id, update_confidence
from mvc_model.models.invoice import create_invoice
from test.mvc_test.helpers import get_confidence_data, get_invoice_data


class TestConfiedenceCRUD(unittest.TestCase):

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
    #-------------------------------------CRUD-CONFIDENCE-SUCCESS------------------------------------#
    def test_create_confidence_success(self):
        create_invoice(self.db, get_invoice_data())
        confidence_data = get_confidence_data()
        created = create_confidence(self.db, confidence_data)
        self.assertIsNotNone(created)
        self.assertIsInstance(created, Confidence)
        self.assertEqual(created.InvoiceId, confidence_data["InvoiceId"])
    
    def test_update_confidence_success(self):
        create_invoice(self.db, get_invoice_data())
        create_confidence(self.db, get_confidence_data())
        updated = update_confidence(self.db, "2910", {"InvoiceTotal": 0.50})
        self.assertIsNotNone(updated)
        self.assertEqual(updated.InvoiceTotal, 0.50)
    
    def test_delete_confidence_success(self):
        create_invoice(self.db, get_invoice_data())
        create_confidence(self.db, get_confidence_data())
        deleted = delete_confidence(self.db, "2910")
        self.assertTrue(deleted)
        after = get_confidence_by_invoice_id(self.db, "2910")
        self.assertIsNone(after)

    def test_get_confidence_by_invoice_id_success(self):
        # create invoice first (FK requirement)
        invoice_data = get_invoice_data()
        create_invoice(self.db, invoice_data)
        # create confidence
        confidence_data = get_confidence_data()
        created = create_confidence(self.db, confidence_data)
        self.assertIsNotNone(created)
        self.assertIsInstance(created, Confidence)
        # get confidence by invoice id
        confidence = get_confidence_by_invoice_id(self.db, invoice_data["InvoiceId"])
        self.assertIsNotNone(confidence)
        self.assertIsInstance(confidence, Confidence)
        self.assertEqual(confidence.InvoiceId, invoice_data["InvoiceId"])


    #-------------------------------------CRUD-CONFIDENCE-FAILUER------------------------------------#
    def test_get_confidence_by_invoice_id_failure(self):
        conf = get_confidence_by_invoice_id(self.db, "NOT_EXISTS")
        self.assertIsNone(conf)

    def test_update_confidence_failure(self):
        updated = update_confidence(self.db, "NOT_EXISTS", {"InvoiceTotal": 0.50})
        self.assertIsNone(updated)
    
    def test_delete_confidence_failure(self):
        deleted = delete_confidence(self.db, "NOT_EXISTS")
        self.assertFalse(deleted)
    
    def test_get_confidence_by_invoice_id_failure(self):
        # try to get confidence for non-existing invoice
        confidence = get_confidence_by_invoice_id(self.db, "NOT_EXISTS")
        self.assertIsNone(confidence)




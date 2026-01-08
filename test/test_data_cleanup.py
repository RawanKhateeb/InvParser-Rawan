import unittest
from datetime import datetime, date, timezone

# Change this import if needed:
from app import format_date_to_iso, clean_amount


class TestFormatDateToIso(unittest.TestCase):

    def test_none_returns_empty_string(self):
        self.assertEqual(format_date_to_iso(None), "")

    def test_empty_string_returns_empty_string(self):
        self.assertEqual(format_date_to_iso(""), "")
        self.assertEqual(format_date_to_iso("   "), "")

    def test_datetime_naive_assumed_utc(self):
        dt = datetime(2012, 3, 6, 10, 30, 0)  # naive
        out = format_date_to_iso(dt)
        # should add UTC tzinfo
        self.assertTrue(out.endswith("+00:00"))
        self.assertIn("2012-03-06T10:30:00", out)

    def test_datetime_with_tz_converted_to_utc(self):
        dt = datetime(2012, 3, 6, 10, 30, 0, tzinfo=timezone.utc)
        out = format_date_to_iso(dt)
        self.assertEqual(out, "2012-03-06T10:30:00+00:00")

    def test_date_object(self):
        d = date(2012, 3, 6)
        out = format_date_to_iso(d)
        self.assertEqual(out, "2012-03-06T00:00:00+00:00")

    def test_iso_string_with_z(self):
        out = format_date_to_iso("2012-03-06T00:00:00Z")
        self.assertEqual(out, "2012-03-06T00:00:00+00:00")

    def test_iso_string_with_offset(self):
        out = format_date_to_iso("2012-03-06T02:00:00+02:00")
        # should convert to UTC -> 00:00:00+00:00
        self.assertEqual(out, "2012-03-06T00:00:00+00:00")

    def test_common_formats(self):
        self.assertEqual(format_date_to_iso("2012-03-06"), "2012-03-06T00:00:00+00:00")
        self.assertEqual(format_date_to_iso("03/06/2012"), "2012-03-06T00:00:00+00:00")
        self.assertEqual(format_date_to_iso("06 Mar 2012"), "2012-03-06T00:00:00+00:00")
        self.assertEqual(format_date_to_iso("06-Mar-2012"), "2012-03-06T00:00:00+00:00")

    def test_unmatched_format_returns_empty_string(self):
        self.assertEqual(format_date_to_iso("not-a-date"), "")
    
    def test_iso_with_T_but_invalid_format_hits_except(self):
        # contains "T" but invalid ISO → ValueError
        out = format_date_to_iso("2012-99-99T99:99:99")
        self.assertEqual(out, "")

    def test_iso_without_timezone_adds_utc(self):
        out = format_date_to_iso("2012-03-06T10:30:00")
        self.assertTrue(out.endswith("+00:00"))




class TestCleanAmount(unittest.TestCase):

    def test_empty_value_returns_empty_string(self):
        self.assertEqual(clean_amount("InvoiceTotal", ""), "")
        self.assertEqual(clean_amount("InvoiceTotal", None), "")

    def test_quantity_returns_int(self):
        self.assertEqual(clean_amount("Quantity", "2"), 2)
        self.assertEqual(clean_amount("Quantity", "  2 "), 2)
        self.assertEqual(clean_amount("Quantity", "1,234"), 1234)
        self.assertEqual(clean_amount("Quantity", "$5"), 5)

    def test_money_fields_return_float(self):
        self.assertEqual(clean_amount("InvoiceTotal", "110"), 110.0)
        self.assertEqual(clean_amount("InvoiceTotal", "110.50"), 110.5)
        self.assertEqual(clean_amount("InvoiceTotal", "$1,234.00"), 1234.0)

    def test_invalid_returns_empty_string(self):
        self.assertEqual(clean_amount("InvoiceTotal", "abc"), "")
        self.assertEqual(clean_amount("Quantity", "two"), "")


if __name__ == "__main__":
    unittest.main()
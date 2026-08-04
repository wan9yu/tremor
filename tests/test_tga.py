"""The Treasury buffer line: a ratio must refuse rather than divide badly.

Pure logic against stubbed responses — no network, no committed data — so this
file may gate collection.
"""
import datetime
import os
import sys
import types
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetchers import tga_days_cash as tga
from support import stub_requests


def _rows(days, balance=1000.0, withdrawal=100.0, field="open_today_bal"):
    """A response shaped like the live one: value in ``field``, other is "null"."""
    out = []
    day = datetime.date(2026, 7, 1)
    made = 0
    while made < days:
        if day.weekday() < 5:
            for kind, value in ((tga._CLOSING, balance), (tga._WITHDRAWALS, withdrawal)):
                row = {"record_date": day.isoformat(), "account_type": kind,
                       "close_today_bal": "null", "open_today_bal": "null"}
                row[field] = str(value)
                out.append(row)
            made += 1
        day += datetime.timedelta(days=1)
    return out


def _reply(rows, status=200):
    return lambda *a, **k: types.SimpleNamespace(
        status_code=status, json=lambda: {"data": rows})


class TestReading(unittest.TestCase):
    def test_the_buffer_is_measured_in_days_of_its_own_outflows(self):
        with stub_requests(tga, _reply(_rows(20, balance=1000.0, withdrawal=200.0))):
            got = tga.fetch_daily()
        self.assertEqual(got["raw_value"], 5.0)
        self.assertEqual(got["obs_date"], max(
            r["record_date"] for r in _rows(20)))

    def test_the_value_is_read_from_whichever_field_carries_it(self):
        """close_today_bal is the literal string 'null' in the live schema."""
        for field in ("open_today_bal", "close_today_bal"):
            with stub_requests(tga, _reply(_rows(20, 1000.0, 200.0, field=field))):
                self.assertEqual(tga.fetch_daily()["raw_value"], 5.0, field)

    def test_both_sides_of_the_ratio_are_kept(self):
        with stub_requests(tga, _reply(_rows(20, balance=900.0, withdrawal=150.0))):
            got = tga.fetch_daily()
        self.assertEqual(got["components"],
                         {"tga_balance_musd": 900.0, "mean_daily_withdrawal_musd": 150.0})

    def test_a_rising_burn_rate_shortens_the_buffer(self):
        """The alarm can arrive through the denominator; that is the point."""
        rows = _rows(20, balance=1000.0, withdrawal=100.0)
        with stub_requests(tga, _reply(rows)):
            calm = tga.fetch_daily()["raw_value"]
        spent = _rows(20, balance=1000.0, withdrawal=250.0)
        with stub_requests(tga, _reply(spent)):
            stressed = tga.fetch_daily()["raw_value"]
        self.assertGreater(calm, stressed)


class TestRefusals(unittest.TestCase):
    def test_a_thin_denominator_is_refused_not_averaged(self):
        with stub_requests(tga, _reply(_rows(5))):
            got = tga.fetch_daily()
        self.assertIsNone(got["raw_value"])
        self.assertIn("business days", got["source_note"])

    def test_a_zero_burn_rate_is_refused(self):
        with stub_requests(tga, _reply(_rows(20, withdrawal=0.0))):
            got = tga.fetch_daily()
        self.assertIsNone(got["raw_value"])
        self.assertIn("not flowing", got["source_note"])

    def test_an_empty_body_is_refused_with_a_reason(self):
        with stub_requests(tga, _reply([])):
            got = tga.fetch_daily()
        self.assertIsNone(got["raw_value"])
        self.assertIn("no TGA closing balance", got["source_note"])

    def test_an_http_error_is_refused_with_a_reason(self):
        with stub_requests(tga, _reply([], status=503)):
            got = tga.fetch_daily()
        self.assertIsNone(got["raw_value"])
        self.assertIn("503", got["source_note"])

    def test_a_crash_never_escapes_as_a_number(self):
        def boom(*a, **k):
            raise Exception("network")
        with stub_requests(tga, boom):
            got = tga.fetch_daily()
        self.assertIsNone(got["raw_value"])


class TestContract(unittest.TestCase):
    def test_it_declares_the_attributes_the_collector_reads(self):
        for attr in ("LINE", "LABEL", "UNIT", "ANOMALY_DIRECTION", "TIER"):
            self.assertTrue(getattr(tga, attr, None), attr)
        self.assertEqual(tga.ANOMALY_DIRECTION, "down")
        self.assertEqual(tga.TIER, 2)

    def test_it_is_collected(self):
        import collect
        self.assertIn(tga, collect.LINES)


if __name__ == "__main__":
    unittest.main()

"""cnh_cny session snap: a Saturday or Sunday quote stamp names no onshore
session, so it must map back to the Friday session it is a frozen copy of.
Stubs the one network entry point and reads no committed record, so this is
safe in the pre-collect gate."""
import datetime
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fetchers import cnh_cny
import support


def _epoch(y, m, d, H, M=0):
    return int(datetime.datetime(y, m, d, H, M, tzinfo=datetime.timezone.utc).timestamp())


class TestSessionDate(unittest.TestCase):
    def test_a_weekday_stamp_is_its_own_session(self):
        self.assertEqual(cnh_cny._session_date(_epoch(2026, 8, 26, 7, 0)),
                         datetime.date(2026, 8, 26))

    def test_a_saturday_stamp_maps_to_friday(self):
        self.assertEqual(cnh_cny._session_date(_epoch(2026, 8, 22, 3, 0)),
                         datetime.date(2026, 8, 21))

    def test_a_sunday_stamp_maps_to_friday(self):
        self.assertEqual(cnh_cny._session_date(_epoch(2026, 8, 23, 22, 26)),
                         datetime.date(2026, 8, 21))


class TestMondayCollectionDedups(unittest.TestCase):
    """The 2026-08-24 payload: both legs re-stamped into Sunday, values
    byte-identical to Friday's close. It must resolve to Friday's session."""

    def _fetch(self, cnh, cnh_t, cny, cny_t):
        quotes = {"USDCNH=X": (cnh, cnh_t), "USDCNY=X": (cny, cny_t)}
        with support.stub_attr(cnh_cny, "_yahoo_quote", lambda sym: quotes[sym]):
            return cnh_cny.fetch_daily()

    def test_the_monday_row_carries_fridays_session(self):
        got = self._fetch(6.7201, _epoch(2026, 8, 23, 22, 26),
                          6.7118, _epoch(2026, 8, 23, 21, 32))
        self.assertEqual(got["obs_date"], "2026-08-21")

    def test_the_preceding_friday_row_carries_the_same_session(self):
        got = self._fetch(6.7201, _epoch(2026, 8, 21, 22, 26),
                          6.7118, _epoch(2026, 8, 21, 21, 32))
        self.assertEqual(got["obs_date"], "2026-08-21")

    def test_the_note_discloses_the_snap(self):
        got = self._fetch(6.7201, _epoch(2026, 8, 23, 22, 26),
                          6.7118, _epoch(2026, 8, 23, 21, 32))
        self.assertIn("session 2026-08-21", got["source_note"])


if __name__ == "__main__":
    unittest.main()

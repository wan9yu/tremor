"""Shape locks for fetchers/gnss.py: a body that is not the GPSJam table is not a reading.

``gnss_interference`` is ONE worldwide ratio, bad aircraft over all aircraft, so
a mis-parsed file does not look broken, it looks like a number. Three ways a 200
response used to become one:

* the two aircraft columns swapped (``bad,good``) read as a ratio near 100%;
* a negative count was summed as if it were a count;
* a body with no header had its FIRST DATA ROW silently dropped, because the
  parse skipped line one unconditionally.

The shape is now required: the exact header, and non-negative integer counts. A
body that fails it is unavailable with a stated reason, like every other source
failure on this record. No quantity threshold is applied: the day's total comes
from a volunteer receiver network and varies by an order of magnitude over the
seeded history, so a floor would be a judgement this test cannot ground.

Pure: no network, no ``data/``. ``requests.get`` is stubbed through
``support.stub_requests``.
"""
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import support  # noqa: E402

from fetchers import gnss  # noqa: E402

HEADER = "hex,count_good_aircraft,count_bad_aircraft"

# Verbatim shape of the file as served (checked live 2022-07-27 .. 2025-09-15).
GOOD = HEADER + "\n8a2a1072b59ffff,100,5\n8a2a1072b5bffff,200,10\n"

# The error-page shape: long enough to pass the fetcher's own length floor.
HTML_PAGE = ("<!DOCTYPE html><html><head><title>Not found</title></head><body>"
             + "<p>this is not the table</p>" * 10 + "</body></html>")


def _response(text, status=200):
    return types.SimpleNamespace(status_code=status, text=text)


class TestCountsFromCsv(unittest.TestCase):
    def test_a_well_formed_file_is_summed(self):
        self.assertEqual(gnss.counts_from_csv(GOOD), (15, 315))

    def test_trailing_whitespace_and_a_final_newline_are_fine(self):
        self.assertEqual(gnss.counts_from_csv(GOOD + "\n\n"), (15, 315))

    def test_a_byte_order_mark_before_the_header_is_tolerated(self):
        self.assertEqual(gnss.counts_from_csv("\ufeff" + GOOD), (15, 315))

    def test_crlf_line_endings_are_tolerated(self):
        self.assertEqual(gnss.counts_from_csv(GOOD.replace("\n", "\r\n")), (15, 315))

    def test_swapped_columns_are_refused(self):
        swapped = "hex,count_bad_aircraft,count_good_aircraft\n8a,5,100\n8b,10,200\n"
        self.assertIsNone(gnss.counts_from_csv(swapped))

    def test_a_body_without_the_header_is_refused_not_one_row_short(self):
        # splitlines()[1:] used to eat the first data row of a header-less file
        self.assertIsNone(gnss.counts_from_csv("8a,100,5\n8b,200,10\n"))

    def test_a_header_only_file_is_empty_not_a_zero_ratio(self):
        self.assertEqual(gnss.counts_from_csv(HEADER + "\n"), (0, 0))

    def test_html_is_refused(self):
        self.assertIsNone(gnss.counts_from_csv(HTML_PAGE))

    def test_an_empty_body_is_refused(self):
        self.assertIsNone(gnss.counts_from_csv(""))

    def test_a_negative_count_skips_that_row_only(self):
        text = HEADER + "\n8a,-50,100\n8b,200,10\n"
        self.assertEqual(gnss.counts_from_csv(text), (10, 210))

    def test_a_non_integer_count_skips_that_row_only(self):
        text = HEADER + "\n8a,abc,1\n8b,200,10\n8c,3.5,1\n"
        self.assertEqual(gnss.counts_from_csv(text), (10, 210))

    def test_a_short_row_is_skipped(self):
        text = HEADER + "\n8a,100\n8b,200,10\n"
        self.assertEqual(gnss.counts_from_csv(text), (10, 210))


class TestFetchDaily(unittest.TestCase):
    def test_a_good_day_is_a_reading(self):
        with support.stub_requests(gnss, lambda url, **kw: _response(GOOD + "x" * 100)):
            # 'x' padding is a malformed row (skipped); length floor is the fetcher's
            out = gnss.fetch_daily()
        self.assertEqual(out["raw_value"], round(15 / 315 * 100.0, 4))
        self.assertIn("15/315", out["source_note"])

    def test_a_wrong_header_is_unavailable_with_the_reason(self):
        swapped = ("hex,count_bad_aircraft,count_good_aircraft\n"
                   + "8a2a1072b59ffff,5,100\n" * 10)
        with support.stub_requests(gnss, lambda url, **kw: _response(swapped)):
            out = gnss.fetch_daily()
        self.assertIsNone(out["raw_value"])
        self.assertNotIn("obs_date", out)
        self.assertIn("unexpected table", out["source_note"])

    def test_an_html_page_is_unavailable_with_the_reason(self):
        with support.stub_requests(gnss, lambda url, **kw: _response(HTML_PAGE)):
            out = gnss.fetch_daily()
        self.assertIsNone(out["raw_value"])
        self.assertIn("unexpected table", out["source_note"])

    def test_a_bad_first_day_falls_through_to_an_earlier_good_one(self):
        calls = []

        def get(url, **kw):
            calls.append(url)
            if len(calls) == 1:
                return _response(HTML_PAGE)
            return _response(GOOD + ("8c,1,0\n" * 20))

        with support.stub_requests(gnss, get):
            out = gnss.fetch_daily()
        self.assertEqual(len(calls), 2)
        self.assertIsNotNone(out["raw_value"])
        self.assertIn("obs_date", out)


if __name__ == "__main__":
    unittest.main()

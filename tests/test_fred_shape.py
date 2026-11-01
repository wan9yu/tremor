"""Parse locks for core/fred.py: a body with no dated rows is not a series.

Incident (2026-10-22): the keyless fredgraph path answered with an HTML error
page. Its Google Fonts ``<link>`` line splits at a comma into
``("    <link href=…Open+Sans:300", "400")``, and ``series()`` — which checked
only that the SECOND field parsed as a float — returned one "observation" of
400 on a date that is not a date. Five lines committed it before a later tool
choked on the malformed ``obs_date``.

The first column is now required to be a strict ``YYYY-MM-DD``. A body with no
surviving row is ``None``, which every caller already reads as unavailable.
No network: ``_spaced_get`` is stubbed, so the module's pacing never runs.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import support

# Verbatim shape of the error page the incident recorded: the obs_date column
# in data/*.csv holds this link's first comma-separated segment, and the 400
# that followed it became the reading.
HTML_ERROR_PAGE = (
    "<!DOCTYPE html>\n"
    "<html>\n"
    "  <head>\n"
    '    <link href="https://fonts.googleapis.com/css?family=Open+Sans:300,'
    '400,600,700&display=swap" rel="stylesheet">\n'
    "  </head>\n"
    "  <body><div>Your request has been blocked.</div></body>\n"
    "</html>\n"
)


def _response(text, status=200):
    class R:
        status_code = status

        def __init__(self, body):
            self.text = body

    return R(text)


class TestSeriesRequiresADatedFirstColumn(unittest.TestCase):
    def _series(self, body):
        from core import fred
        with support.stub_attr(fred, "_spaced_get",
                               lambda params, timeout=15: _response(body)):
            return fred.series("SOFR")

    def test_an_html_error_page_is_not_a_series(self):
        self.assertIsNone(self._series(HTML_ERROR_PAGE))

    def test_a_rejected_body_reads_as_unavailable_end_to_end(self):
        from core import fred
        with support.stub_attr(fred, "_spaced_get",
                               lambda params, timeout=15:
                               _response(HTML_ERROR_PAGE)):
            out = fred.reading("SOFR")
        self.assertIsNone(out["raw_value"])
        self.assertNotIn("obs_date", out)
        self.assertIn("unavailable", out["source_note"])

    def test_a_dated_csv_still_parses(self):
        body = ("observation_date,SOFR\n"
                "2026-10-20,4.10\n"
                "2026-10-21,4.09\n")
        self.assertEqual(self._series(body),
                         [("2026-10-20", 4.10), ("2026-10-21", 4.09)])

    def test_only_dated_rows_survive_a_mixed_body(self):
        body = ("observation_date,SOFR\n"
                "2026-10-20,4.10\n"
                "    <link href=\"https://fonts.googleapis.com/css?"
                "family=Open+Sans:300,400,600,700&display=swap\" "
                "rel=\"stylesheet\">\n"
                "20261022,4.08\n"      # basic format: date.fromisoformat accepts it
                "٢٠٢٦-10-22,4.11\n"    # Arabic-Indic digits: \d matches, [0-9] does not
                "２０２６-10-23,4.12\n"  # full-width digits: same mutant
                "2026-02-31,4.07\n"    # right shape, impossible day
                "2026-10-23,.\n")      # a missing observation, not a row
        self.assertEqual(self._series(body), [("2026-10-20", 4.10)])

    def test_a_non_200_response_is_still_unavailable(self):
        # A well-formed body, so only the status branch can reject it.
        body = "observation_date,SOFR\n2026-10-20,4.10\n"
        from core import fred
        with support.stub_attr(fred, "_spaced_get",
                               lambda params, timeout=15:
                               _response(body, status=429)):
            self.assertIsNone(fred.series("SOFR"))


if __name__ == "__main__":
    unittest.main()

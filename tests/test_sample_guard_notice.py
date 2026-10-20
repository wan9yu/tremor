"""The sample-hour refusal notice reads committed rows. It does not score.

A counted line that declares a sample-hour target is named when the row this
run committed starts with the guard sentence. Status is not consulted: a
weekend closure can still carry that sentence. An on-time row, a source
failure, a tier-2 timeout, and an older refusal are not named. No network.
"""
import csv
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from fetchers import flights  # noqa: E402
from tools.sample_guard_notice import notice_line, refused_lines  # noqa: E402

GUARD = "no reading: sampled +0.6h from the 22:30Z target (CI delayed past the sleep window)"
ON_TIME = "ADS-B regions [W/C Europe=165] [sampled 22:30:00Z]"
SOURCE_DARK = "no reading: fetcher returned a nan — not scored"
HKMA_DARK = "HKMA request failed: ReadTimeout after 25.7s"
WEEKEND = "no new observation: FX weekend, both legs frozen"


def _mod(line, tier=1, target=22.5):
    attrs = {"LINE": line}
    if target is not False:
        attrs["SAMPLE_TARGET_UTC_H"] = target
    if tier is not None:
        attrs["TIER"] = tier
    return SimpleNamespace(**attrs)


class TestRefusedLines(unittest.TestCase):
    def test_guard_sentence_on_the_china_date_hits(self):
        rows = {"cnh_cny": [{"date": "2026-10-13", "status": "dark",
                             "source_note": GUARD}]}
        self.assertEqual(
            refused_lines([_mod("cnh_cny")], rows, "2026-10-13"),
            ["cnh_cny"])

    def test_same_sentence_on_the_previous_utc_date_does_not_hit(self):
        # 23:05Z is still the previous UTC date; the committed row date is China.
        rows = {"cnh_cny": [{"date": "2026-10-08", "status": "dark",
                             "source_note": GUARD}]}
        self.assertEqual(refused_lines([_mod("cnh_cny")], rows, "2026-10-09"), [])

    def test_on_time_sample_stamp_does_not_hit(self):
        rows = {"flights": [{"date": "2026-10-12", "status": "scoring",
                             "source_note": ON_TIME}]}
        self.assertEqual(refused_lines([_mod("flights")], rows, "2026-10-12"), [])

    def test_source_failure_dark_does_not_hit(self):
        rows = {"flights": [{"date": "2026-10-13", "status": "dark",
                             "source_note": SOURCE_DARK}]}
        self.assertEqual(refused_lines([_mod("flights")], rows, "2026-10-13"), [])

    def test_tier2_timeout_does_not_hit(self):
        rows = {"hkma_aggr_balance": [{"date": "2026-10-13", "status": "dark",
                                       "source_note": HKMA_DARK}]}
        self.assertEqual(
            refused_lines([_mod("hkma_aggr_balance", tier=2, target=False)],
                          rows, "2026-10-13"),
            [])

    def test_weekend_closed_with_the_guard_sentence_hits(self):
        rows = {"cnh_cny": [{"date": "2026-10-11", "status": "closed",
                             "source_note": GUARD}]}
        self.assertEqual(
            refused_lines([_mod("cnh_cny")], rows, "2026-10-11"),
            ["cnh_cny"])

    def test_ordinary_weekend_closure_does_not_hit(self):
        rows = {"cnh_cny": [{"date": "2026-10-11", "status": "closed",
                             "source_note": WEEKEND}]}
        self.assertEqual(refused_lines([_mod("cnh_cny")], rows, "2026-10-11"), [])

    def test_older_guard_row_does_not_hit_a_later_on_time_day(self):
        rows = {"cnh_cny": [
            {"date": "2026-10-09", "status": "dark", "source_note": GUARD},
            {"date": "2026-10-10", "status": "scoring", "source_note": ON_TIME},
        ]}
        self.assertEqual(refused_lines([_mod("cnh_cny")], rows, "2026-10-10"), [])

    def test_missing_tier_counts_as_primary(self):
        # flights declares no TIER; collect treats that as 1.
        self.assertFalse(hasattr(flights, "TIER"))
        rows = {"flights": [{"date": "2026-10-13", "status": "dark",
                             "source_note": GUARD}]}
        self.assertEqual(
            refused_lines([flights], rows, "2026-10-13"),
            ["flights"])


class TestNoticeLine(unittest.TestCase):
    def test_reads_only_the_named_date_and_formats_the_shell_line(self):
        with tempfile.TemporaryDirectory() as directory:
            self._write(directory, "cnh_cny", [
                {"date": "2026-10-09", "source_note": GUARD},
                {"date": "2026-10-10", "source_note": ON_TIME},
            ])
            self._write(directory, "flights", [
                {"date": "2026-10-13", "source_note": GUARD},
            ])
            modules = [_mod("flights"), _mod("cnh_cny")]
            self.assertEqual(notice_line(directory, "2026-10-10", modules), "")
            self.assertEqual(
                notice_line(directory, "2026-10-13", modules),
                "2026-10-13 flights")
            self.assertEqual(
                notice_line(directory, "2026-10-09", modules),
                "2026-10-09 cnh_cny")

    def test_missing_file_is_not_a_hit(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                notice_line(directory, "2026-10-13", [_mod("cnh_cny")]), "")

    def _write(self, directory, line, rows):
        path = os.path.join(directory, line + ".csv")
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["date", "source_note"])
            writer.writeheader()
            writer.writerows(rows)


class TestWorkflowPlacement(unittest.TestCase):
    def test_notice_step_sits_before_the_failure_alarm(self):
        path = os.path.join(ROOT, ".github", "workflows", "daily.yml")
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        notice = text.index("Notice a counted sample-hour refusal")
        alarm = text.index("Raise the alarm on failure")
        self.assertLess(notice, alarm)
        block = text[notice:alarm]
        self.assertNotIn("if: always()", block)
        self.assertNotIn("continue-on-error", block)
        self.assertNotIn("date -u", block)
        self.assertNotIn("writes no row", block)
        self.assertIn("exit 0", block)
        self.assertIn("|| exit 1", block)

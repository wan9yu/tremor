"""The merge path that adds a component day the capture never recorded.

The 2026-10-28..10-31 PortWatch outage left 2026-10-18..10-21 with no line row at
all, so the default backfill path — which derives its dates from the LINE record —
cannot reach them: there is nothing to derive a date from. ``--dates`` names them.

The whole risk of this path is that it rewrites a capture. The component file is
the only surviving per-strait breakdown of days the line already scored, and
``collect._write_rows`` replaces the file wholesale, so a merge that dropped or
re-rendered an existing day would destroy evidence silently. These tests pin:
the existing days come out byte-identical, a day already present is refused
rather than rewritten, and a partial or ragged answer is refused rather than
written.

Pure: a temp directory stands in for ``data/components`` and ``fetch_range`` is
stubbed, so nothing here touches ``data/`` or the network.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))

import support  # noqa: E402

from tools import backfill_components as bc  # noqa: E402


def _panel(day, base=1.0):
    return {f"Strait {i}": base + i for i in range(3)}


class TestMergeNeverRewritesACapture(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = self._tmp.name
        self.path = os.path.join(self.dir, "chokepoint_breadth.csv")
        # one captured day, already in the file
        bc.collect._write_rows(self.path, bc.collect.COMPONENT_HEADER, [
            {"date": "2026-10-17", "component": "Strait 0", "value": "10"},
            {"date": "2026-10-17", "component": "Strait 1", "value": "11"},
            {"date": "2026-10-17", "component": "Strait 2", "value": "12"},
        ])

    def _run(self, dates, recovered):
        with support.stub_attr(bc, "_components_path", lambda: self.path), \
                support.stub_attr(bc, "fetch_range",
                                  lambda *a, **k: recovered):
            return bc.add_dates(list(dates), dry=False)

    def _rows(self):
        with open(self.path, newline="", encoding="utf-8") as fh:
            return fh.read()

    def test_a_new_day_is_added_and_the_captured_one_is_byte_identical(self):
        before = self._rows()
        captured = [ln for ln in before.splitlines() if ln.startswith("2026-10-17,")]
        code = self._run(["2026-10-18"], {"2026-10-18": _panel("2026-10-18", 20.0)})
        self.assertEqual(code, 0)
        after = self._rows()
        for line in captured:
            self.assertIn(line, after.splitlines(), "a captured row moved or changed")
        self.assertEqual(after.count("2026-10-18,"), 3)

    def test_a_date_already_present_is_refused(self):
        before = self._rows()
        self.assertEqual(self._run(["2026-10-17"], {"2026-10-17": _panel("2026-10-17")}), 2)
        self.assertEqual(self._rows(), before, "a refused run must not write")

    def test_a_date_the_source_does_not_serve_is_refused(self):
        before = self._rows()
        self.assertEqual(self._run(["2026-10-18", "2026-10-19"],
                                   {"2026-10-18": _panel("2026-10-18")}), 2)
        self.assertEqual(self._rows(), before)

    def test_a_ragged_panel_is_refused(self):
        before = self._rows()
        self.assertEqual(self._run(["2026-10-18", "2026-10-19"],
                                   {"2026-10-18": _panel("2026-10-18"),
                                    "2026-10-19": {"Strait 0": 1.0}}), 2)
        self.assertEqual(self._rows(), before)

    def test_an_empty_source_answer_is_refused(self):
        before = self._rows()
        self.assertEqual(self._run(["2026-10-18"], {}), 2)
        self.assertEqual(self._rows(), before)

    def test_dry_run_writes_nothing(self):
        before = self._rows()
        with support.stub_attr(bc, "_components_path", lambda: self.path), \
                support.stub_attr(bc, "fetch_range",
                                  lambda *a, **k: {"2026-10-18": _panel("2026-10-18")}):
            self.assertEqual(bc.add_dates(["2026-10-18"], dry=True), 0)
        self.assertEqual(self._rows(), before)

    def test_several_new_days_are_all_added_and_sorted(self):
        code = self._run(["2026-10-19", "2026-10-18"],
                         {"2026-10-18": _panel("2026-10-18"),
                          "2026-10-19": _panel("2026-10-19")})
        self.assertEqual(code, 0)
        dates = [ln.split(",")[0] for ln in self._rows().splitlines()[1:]]
        self.assertEqual(dates, sorted(dates))
        self.assertEqual(set(dates), {"2026-10-17", "2026-10-18", "2026-10-19"})


class TestArgumentParsing(unittest.TestCase):
    def test_a_malformed_date_is_refused(self):
        self.assertEqual(bc.main(["--dates=20261019"]), 2)

    def test_an_empty_dates_argument_falls_through_to_the_default_path(self):
        # --dates= with nothing after it must not be read as a request for the
        # date named "" ; the default path reports and returns 0 under --dry-run
        with support.stub_attr(bc, "observation_dates", lambda line: ["2026-10-17"]):
            self.assertEqual(bc.main(["--dry-run", "--dates="]), 0)


if __name__ == "__main__":
    unittest.main()

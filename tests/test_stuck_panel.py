"""The stuck-strait panel serves the level layer to the dashboard, and must do it
from OUTSIDE the scoring path.

The panel exists because the scored chokepoint line, a sum over 28 straits, is
blind to one or two small straits going silent (radar.md round 12). Its reporter
reads the derived levels.csv and writes docs/data/stuck.csv -- but the same
firewall that keeps the level layer out of the scorer (tests/test_level.py,
tests/test_side_channel.py) must keep this presentation reader out too: a file the
scorer reads becomes an input to a verdict. These tests are pure logic and read no
committed record, so they are safe in the pre-collect gate.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _src(rel):
    with open(os.path.join(ROOT, rel)) as f:
        return f.read()


class TestStuckPanelIsOutsideTheScoringPath(unittest.TestCase):
    SCORING_PATH = ["collect.py", os.path.join("core", "normalize.py"),
                    os.path.join("core", "clock.py")]

    def test_scoring_path_never_names_the_panel(self):
        for rel in self.SCORING_PATH:
            source = _src(rel)
            self.assertNotIn("stuck_panel", source,
                             f"{rel} imports the presentation reporter")
            self.assertNotIn("stuck.csv", source,
                             f"{rel} names the served panel file")

    def test_stuck_is_served_deliberately_not_auto_mirrored(self):
        """Like levels.csv, the panel is served by its own reporter, never by the
        collect mirror allow-list -- so a scoring-path change can never start
        serving or reading it by forgetting to exclude it."""
        import collect
        self.assertNotIn("stuck.csv", collect.MIRRORED)

    def test_the_reporter_writes_no_verdict(self):
        source = _src(os.path.join("tools", "stuck_panel.py"))
        self.assertNotIn("summary.csv", source, "the reporter touches the summary")
        self.assertNotIn("write_line", source, "the reporter writes a scored line")
        self.assertNotIn("score_row", source, "the reporter produces a verdict")


class TestBuildPanel(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import stuck_panel
        self.build = stuck_panel.build_panel

    def test_count_since_pct_and_the_pinned_reference(self):
        # `trail_median` and `reference` are the level layer's own numbers
        # (transits/day); the panel must carry them through so the page can
        # state what the ratio compares, not just the percentage.
        rows = [
            {"date": "2026-04-06", "component": "Strait of Hormuz", "event": "open",
             "trail_median": "9", "reference": "72", "ratio": "0.125"},
            {"date": "2026-04-07", "component": "Strait of Hormuz", "event": "hold",
             "trail_median": "8.6", "reference": "72", "ratio": "0.120"},
            {"date": "2026-07-26", "component": "Kerch Strait", "event": "open",
             "trail_median": "6", "reference": "72", "ratio": "0.083"},
            {"date": "2026-07-26", "component": "Strait of Hormuz", "event": "hold",
             "trail_median": "5", "reference": "72", "ratio": "0.070"},
            {"date": "2026-07-27", "component": "Kerch Strait", "event": "hold",
             "trail_median": "0", "reference": "72", "ratio": "0.000"},
            {"date": "2026-07-27", "component": "Strait of Hormuz", "event": "hold",
             "trail_median": "5", "reference": "72", "ratio": "0.070"},
        ]
        out = self.build(rows, stale_now={"Kerch Strait"})
        latest = "2026-07-27"
        now = [r for r in out if r["date"] == latest]
        # two straits stuck quiet on the latest day -- the count the sum cannot show
        self.assertEqual(len(now), 2)
        kerch = next(r for r in now if r["component"] == "Kerch Strait")
        self.assertEqual(kerch["since"], "2026-07-26")   # since = its own open date
        self.assertEqual(kerch["pct"], 0)                # 0.000 -> 0%
        self.assertEqual(kerch["stale"], "1")            # in stale_now, on the latest date
        self.assertEqual(kerch["trail_median"], "0")     # carried, not recomputed
        self.assertEqual(kerch["reference"], "72")       # the PINNED reference
        self.assertEqual(kerch["open_days"], "2")        # 07-26..07-27 inclusive
        hormuz = next(r for r in now if r["component"] == "Strait of Hormuz")
        self.assertEqual(hormuz["since"], "2026-04-06")
        self.assertEqual(hormuz["pct"], 7)               # 0.070 -> 7%
        self.assertEqual(hormuz["stale"], "")            # not stale, though on the latest date
        self.assertEqual(hormuz["trail_median"], "5")    # latest HOLD row, not the open day
        self.assertEqual(hormuz["reference"], "72")
        self.assertEqual(hormuz["open_days"], "113")     # 04-06..07-27 inclusive

    def test_a_stalled_open_state_is_carried_with_the_stale_flag(self):
        # Kerch stops being served after 07-26 while Hormuz keeps advancing.
        # The state is still open, so it must stay in the day's count on the
        # panel's latest date -- flagged stale, with its own last observed
        # values, never interpolated.
        rows = [
            {"date": "2026-07-26", "component": "Kerch Strait", "event": "open",
             "trail_median": "6", "reference": "12", "ratio": "0.500"},
            {"date": "2026-07-26", "component": "Strait of Hormuz", "event": "open",
             "trail_median": "9", "reference": "72", "ratio": "0.125"},
            {"date": "2026-07-27", "component": "Strait of Hormuz", "event": "hold",
             "trail_median": "9", "reference": "72", "ratio": "0.125"},
            {"date": "2026-07-28", "component": "Strait of Hormuz", "event": "hold",
             "trail_median": "8", "reference": "72", "ratio": "0.111"},
        ]
        out = self.build(rows, stale_now={"Kerch Strait"})
        latest = [r for r in out if r["date"] == "2026-07-28"]
        self.assertEqual([r["component"] for r in latest],
                         ["Kerch Strait", "Strait of Hormuz"])
        kerch = latest[0]
        self.assertEqual(kerch["stale"], "1")
        self.assertEqual(kerch["trail_median"], "6")   # its last observed value
        self.assertEqual(kerch["reference"], "12")
        self.assertEqual(kerch["since"], "2026-07-26")
        self.assertEqual(kerch["open_days"], "3")      # carried to the panel date
        hormuz = latest[1]
        self.assertEqual(hormuz["stale"], "")
        self.assertEqual(hormuz["trail_median"], "8")

    def test_stale_flag_only_on_the_latest_date(self):
        rows = [
            {"date": "2026-07-26", "component": "Kerch Strait", "event": "open", "ratio": "0.083"},
            {"date": "2026-07-27", "component": "Kerch Strait", "event": "hold", "ratio": "0.000"},
        ]
        out = self.build(rows, stale_now={"Kerch Strait"})
        self.assertEqual([r["stale"] for r in out], ["", "1"])

    def test_clear_ends_the_count(self):
        rows = [
            {"date": "2026-05-14", "component": "Kerch Strait", "event": "open", "ratio": "0.385"},
            {"date": "2026-05-19", "component": "Kerch Strait", "event": "clear", "ratio": "0.846"},
        ]
        out = self.build(rows)
        # the open day is counted; the clear day is not a stuck day
        self.assertEqual([r["date"] for r in out], ["2026-05-14"])

    def test_empty(self):
        self.assertEqual(self.build([]), [])


if __name__ == "__main__":
    unittest.main()

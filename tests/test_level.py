"""The level and drift rules, locked: pin on open, clear only against the pin.

Pure logic on synthetic series — no committed data is asserted here, so this
file may gate collection.
"""
import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))

import support  # noqa: E402  (needs the sys.path insert above)

from tools import drift_layer, level_layer  # noqa: E402


def _series(values, start="2025-01-01"):
    day = datetime.date.fromisoformat(start)
    out = []
    for v in values:
        out.append((day.isoformat(), float(v)))
        day += datetime.timedelta(days=1)
    return out


class TestLevelRule(unittest.TestCase):
    def test_a_persistent_collapse_opens_and_pins(self):
        events = level_layer.walk(_series([70.0] * 200 + [10.0] * 40))
        opens = [e for e in events if e[1] == "open"]
        self.assertEqual(len(opens), 1)
        date, _, trail, ref, ratio = opens[0]
        # At least 14 breach days of persistence before the state opens (more
        # in practice: the trailing median itself takes days to cross).
        days_in = (datetime.date.fromisoformat(date)
                   - datetime.date.fromisoformat("2025-01-01")).days
        self.assertGreaterEqual(days_in, 200 + 14)
        self.assertEqual(ref, 70.0)
        self.assertLess(ratio, 0.2)
        # The state holds daily until it clears; the pin does not drift even
        # though the collapsed level is now most of the trailing year.
        holds = [e for e in events if e[1] == "hold"]
        self.assertTrue(holds)
        self.assertTrue(all(e[3] == 70.0 for e in holds))

    def test_recovery_clears_against_the_pin(self):
        events = level_layer.walk(
            _series([70.0] * 200 + [10.0] * 60 + [70.0] * 20))
        kinds = [e[1] for e in events if e[1] != "hold"]
        self.assertEqual(kinds, ["open", "clear"])
        clear = [e for e in events if e[1] == "clear"][0]
        self.assertGreaterEqual(clear[2], level_layer.CLEAR_RATIO * 70.0)

    def test_a_storm_week_does_not_open(self):
        events = level_layer.walk(_series([70.0] * 200 + [5.0] * 5 + [70.0] * 60))
        self.assertEqual([e for e in events if e[1] == "open"], [])

    def test_a_small_strait_cannot_produce_a_state(self):
        events = level_layer.walk(_series([3.0] * 200 + [0.0] * 60))
        self.assertEqual(events, [])

    def test_no_reference_means_no_state(self):
        # Too young: nothing older than 60 days by enough to build a reference.
        events = level_layer.walk(_series([70.0] * 70 + [10.0] * 20))
        self.assertEqual([e for e in events if e[1] == "open"], [])

    def test_scoring_code_never_reads_the_level_file(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for rel in ("collect.py", os.path.join("core", "normalize.py")):
            with open(os.path.join(root, rel)) as f:
                source = f.read()
            for name in ("levels", "drifts"):
                self.assertNotIn(name, source,
                                 f"{rel} must not know the {name} layer exists")


class TestDriftRule(unittest.TestCase):
    """Two-sided, pinned, and slow enough that only a real step opens a state."""

    def _flat(self, n, value=1.0):
        return _series([value] * n)

    def test_a_sustained_step_up_opens_and_pins(self):
        events = drift_layer.walk(_series([1.0] * 400 + [1.8] * 80))
        opens = [e for e in events if e[1] == "open"]
        self.assertEqual(len(opens), 1)
        self.assertEqual(opens[0][2], "high")
        self.assertEqual(opens[0][4], 1.0)          # reference pinned at the old level
        holds = [e for e in events if e[1] == "hold"]
        self.assertTrue(all(e[4] == 1.0 for e in holds), "the pin drifted")

    def test_a_sustained_step_down_opens_low(self):
        events = drift_layer.walk(_series([1.0] * 400 + [0.5] * 80))
        opens = [e for e in events if e[1] == "open"]
        self.assertEqual([e[2] for e in opens], ["low"])

    def test_a_three_week_excursion_does_not_open(self):
        events = drift_layer.walk(_series([1.0] * 400 + [1.8] * 21 + [1.0] * 60))
        self.assertEqual([e for e in events if e[1] == "open"], [])

    def test_a_return_clears_the_state(self):
        events = drift_layer.walk(_series([1.0] * 400 + [1.8] * 90 + [1.0] * 40))
        self.assertEqual([e[1] for e in events if e[1] != "hold"], ["open", "clear"])

    def test_a_series_crossing_zero_is_refused(self):
        """A ratio to a median is meaningless there; say nothing rather than lie."""
        self.assertEqual(drift_layer.walk(_series([-1.0, 0.0, 1.0] * 200)), [])


class TestDriftDateGuard(unittest.TestCase):
    """A malformed obs_date is dropped at series_for, never handed to walk.

    walk parses every key it is given, so one bad row in one line crashed the
    whole derive step on that line's own record. The guard sits in series_for
    rather than walk because walk knows no line name, and a filter applied
    after ``ords = [...]`` would misalign ``ords``/``values`` and could write
    the bad string into drifts.csv's date column.
    """

    def test_the_predicate_is_strict_iso_shape_and_a_real_calendar_day(self):
        for good in ("2026-10-22", "2026-02-28", "2024-02-29"):
            self.assertTrue(drift_layer.is_strict_date(good), good)
        # basic format is what date.fromisoformat alone would accept
        for bad in ("20261022", "", "2026-1-22", " 2026-10-22", "2026-10-22T00:00:00",
                    "2026-02-31", "2026-13-01", "not a date", None):
            self.assertFalse(drift_layer.is_strict_date(bad), repr(bad))

    def test_a_blank_obs_date_keeps_the_row_date_and_a_bad_one_is_dropped(self):
        rows = [
            # live lines (flights, capital_premium) score rows with no obs_date
            {"date": "2026-08-01", "obs_date": "", "raw_value": "1.5"},
            {"date": "2026-08-03", "obs_date": "2026-08-02", "raw_value": "1.6"},
            # the incident: an HTML error page arrived in the obs_date column
            {"date": "2026-10-22",
             "obs_date": '<link href="https://fonts.googleapis.com/css?family=Open+Sans:300',
             "raw_value": "0.9"},
            {"date": "2026-08-04", "obs_date": "20260803", "raw_value": "1.7"},
            # a dark row carries no reading, so nothing is being dropped
            {"date": "2026-08-05", "obs_date": "garbage", "raw_value": ""},
        ]
        series, skipped = drift_layer.series_from_rows(rows)
        self.assertEqual(series, [("2026-08-01", 1.5), ("2026-08-02", 1.6)])
        self.assertEqual(skipped, 2)
        # the point of the guard: the surviving series is safe to walk
        self.assertEqual(drift_layer.walk(series), [])

    def test_series_for_reports_what_it_dropped(self):
        rows = [
            {"date": "2026-08-01", "obs_date": "", "raw_value": "2"},
            {"date": "2026-08-02", "obs_date": "<link href=\"https://example.invalid\">",
             "raw_value": "3"},
        ]
        with support.stub_attr(drift_layer.seedlib, "read_line", lambda line: rows):
            series, skipped = drift_layer.series_for("stub")
        self.assertEqual(series, [("2026-08-01", 2.0)])
        self.assertEqual(skipped, 1)


if __name__ == "__main__":
    unittest.main()

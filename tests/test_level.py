"""The level and drift rules, locked: pin on open, clear only against the pin.

Pure logic on synthetic series — no committed data is asserted here, so this
file may gate collection.
"""
import contextlib
import datetime
import io
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


class TestLevelDateGuard(unittest.TestCase):
    """A component row with an unusable date is dropped at the read, counted.

    ``walk`` and ``stale_note`` both parse every date they are handed with
    ``date.fromisoformat``, so one mangled row in the component record would
    abort the whole derive step, and a basic-form ``20261002`` would be
    accepted silently by that parser on 3.11+ and then sort as a distinct key.
    Same rule and same shape as ``TestDriftDateGuard``: the guard sits where
    rows become series, not inside ``walk``.
    """

    @staticmethod
    def rows():
        return [
            {"date": "2026-10-01", "component": "Strait A", "value": "10"},
            {"date": "<!DOCTYPE html>", "component": "Strait A", "value": "5"},
            {"date": "20261002", "component": "Strait A", "value": "6"},
            {"date": "", "component": "Strait A", "value": "7"},
            {"date": "2026-10-03", "component": "Strait A", "value": "7"},
            {"date": "2026-10-01", "component": "Strait B", "value": "3"},
        ]

    def test_unusable_dates_are_dropped_and_counted_per_the_whole_record(self):
        by_component, skipped = level_layer.series_from_rows(self.rows())
        self.assertEqual(skipped, 3)
        self.assertEqual(by_component, {
            "Strait A": [("2026-10-01", 10.0), ("2026-10-03", 7.0)],
            "Strait B": [("2026-10-01", 3.0)],
        })

    def test_the_surviving_series_is_safe_to_walk(self):
        by_component, _ = level_layer.series_from_rows(self.rows())
        for series in by_component.values():
            self.assertEqual(level_layer.walk(series), [])

    def test_series_are_sorted_oldest_first(self):
        rows = [{"date": "2026-10-03", "component": "X", "value": "1"},
                {"date": "2026-10-01", "component": "X", "value": "2"}]
        by_component, skipped = level_layer.series_from_rows(rows)
        self.assertEqual(skipped, 0)
        self.assertEqual([d for d, _ in by_component["X"]],
                         ["2026-10-01", "2026-10-03"])

    def test_a_clean_record_drops_nothing(self):
        rows = [{"date": "2026-10-01", "component": "X", "value": "1.5"}]
        self.assertEqual(level_layer.series_from_rows(rows),
                         ({"X": [("2026-10-01", 1.5)]}, 0))

    def test_compute_reports_what_it_dropped(self):
        with support.stub_attr(level_layer.collect, "_read_rows",
                               lambda path: self.rows()):
            rows, skipped = level_layer.compute()
        self.assertEqual(rows, [])
        self.assertEqual(skipped, 3)

    def _report(self, rows):
        """``(exit code, stdout)`` of ``level_layer.main(["--report"])`` over ``rows``."""
        buf = io.StringIO()
        with support.stub_attr(level_layer.collect, "_read_rows", lambda path: rows), \
                contextlib.redirect_stdout(buf):
            code = level_layer.main(["--report"])
        return code, buf.getvalue()

    def test_the_report_says_how_many_rows_the_guard_dropped(self):
        code, out = self._report(self.rows())
        self.assertEqual(code, 0)
        self.assertIn("3 component row(s) dropped (unusable date)", out)

    def test_the_report_is_silent_when_nothing_was_dropped(self):
        clean = [r for r in self.rows() if r["date"].startswith("2026-")]
        _, out = self._report(clean)
        self.assertNotIn("dropped", out)

    def test_last_seen_ignores_unusable_dates(self):
        # stale_note parses both dates it is given; a mangled "newest" would
        # raise there, and a mangled string can also sort above every real date
        rows = self.rows() + [{"date": "~~junk", "component": "Strait B", "value": "1"}]
        with support.stub_attr(level_layer.collect, "_read_rows",
                               lambda path: list(rows)):
            newest, per_component = level_layer.last_seen()
        self.assertEqual(newest, "2026-10-03")
        self.assertEqual(per_component, {"Strait A": "2026-10-03",
                                         "Strait B": "2026-10-01"})
        self.assertEqual(level_layer.stale_note(newest, per_component["Strait B"]),
                         "  [NO LONGER SERVED: last seen 2026-10-01, 2 observation days ago "
                         "\u2014 this state cannot clear because nothing is watching it]")


if __name__ == "__main__":
    unittest.main()

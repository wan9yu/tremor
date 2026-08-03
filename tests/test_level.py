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

import drift_layer
import level_layer


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


if __name__ == "__main__":
    unittest.main()

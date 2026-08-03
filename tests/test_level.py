"""The level layer's rule, locked: pin on open, clear only against the pin.

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
                self.assertNotIn("levels", f.read(),
                                 f"{rel} must not know the level layer exists")


if __name__ == "__main__":
    unittest.main()
